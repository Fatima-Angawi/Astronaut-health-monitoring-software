"""
Engine step 2: rules. Applies every enabled rule in the `rules` table (loaded from rules.json by export_kb.py)
to daily_features (written by features.py) and writes one alert per rule hit.

Operators follow the "_ops" block of rules.json exactly:
  <, >, <=, >=, ==     compare the feature with the threshold
  flag                 the feature is a 0/1 flag; fires when >= threshold (1)
  baseline+2sd         the feature's z vs personal baseline (features.py: <metric>_z) > threshold
  below_baseline_by    window mean of the feature is below the personal baseline median by >= threshold
  consecutive          this indicator's yellow on `threshold` days in a row
  persists             this indicator's yellow for `window_days` days in a row
  and_yellow           this indicator's yellow AND the indicator named in `metric` yellow on the same day
  before_critical      this indicator's orange on a day with a critical event today or tomorrow (critical_next_24h)
Composite operators run after the simple ones, and before_critical last, because they build on them.

Writes: alerts rows with source_engine = 'rule' (earlier rule alerts are deleted first, so a rerun is clean).
escalated_to and action are left empty: triage.py and recommendations.py fill them.
Cabin-wide rules (R03c, R21b) are written per astronaut here; triage.py merges them into one crew alert.

Usage: python engine/rules.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"
COMPARE = {"<": np.less, ">": np.greater, "<=": np.less_equal, ">=": np.greater_equal, "==": np.equal}
SIMPLE = set(COMPARE) | {"flag", "baseline+2sd", "below_baseline_by"}
COMPOSITE = ["and_yellow", "consecutive", "persists"]
LAST = ["before_critical"]


def run_length(s):
    """Days in a row the boolean series has been true, per astronaut (index: astronaut_id, mission_day)."""
    def one(x):
        g = (~x).cumsum()
        return x.astype(int).groupby(g).cumsum()
    return s.groupby(level=0, group_keys=False).apply(one)


def main():
    con = sqlite3.connect(DB, timeout=30)
    rules = pd.read_sql("SELECT * FROM rules WHERE enabled = 1", con)
    if rules.empty:
        raise SystemExit("rules table is empty: run knowledge_base/export_kb.py first")
    f = pd.read_sql("SELECT * FROM daily_features", con).pivot_table(
        index=["astronaut_id", "mission_day"], columns="metric", values="value")
    base = pd.read_sql("SELECT astronaut_id, metric, median FROM baselines", con)
    med = {(r.astronaut_id, r.metric): r.median for r in base.itertuples()}
    dates = dict(pd.read_sql("SELECT mission_day, date FROM mission_timeline", con).values)
    idx = f.index
    false = pd.Series(False, index=idx)

    hits = {}                      # rule_id -> boolean Series
    level_of = {}                  # (indicator, level) -> boolean Series (any rule of that level)
    detail = {}                    # rule_id -> Series of the value that was compared (for the reason text)
    skipped = []

    def mark(r, s, val=None):
        s = s.fillna(False).astype(bool)
        hits[r.rule_id] = s
        detail[r.rule_id] = val
        key = (r.indicator_id, r.level)
        level_of[key] = level_of.get(key, false) | s

    for phase in (SIMPLE, COMPOSITE, LAST):
        for r in rules[rules.op.isin(phase)].itertuples():
            op, m, t = r.op, r.metric, r.threshold
            if op in COMPARE or op == "flag":
                if m not in f:
                    skipped.append(f"#{r.rule_id} {r.indicator_id} {m}: feature missing"); continue
                v = f[m]
                mark(r, v >= (t if t is not None else 1) if op == "flag" else COMPARE[op](v, t), v)
            elif op == "baseline+2sd":
                z = f.get(f"{m}_z")
                if z is None:
                    skipped.append(f"#{r.rule_id} {r.indicator_id} {m}_z: feature missing"); continue
                mark(r, z > t, z)
            elif op == "below_baseline_by":
                if m not in f:
                    skipped.append(f"#{r.rule_id} {r.indicator_id} {m}: feature missing"); continue
                w = int(r.window_days or 1)
                mean = f[m].groupby(level=0, group_keys=False).apply(lambda x: x.rolling(w, min_periods=w).mean())
                b = pd.Series([med.get((a, m), np.nan) for a, _ in idx], index=idx)
                drop = b - mean
                mark(r, drop >= t, drop)
            elif op == "and_yellow":
                mark(r, level_of.get((r.indicator_id, "yellow"), false) & level_of.get((m, "yellow"), false))
            elif op == "consecutive":
                mark(r, run_length(level_of.get((r.indicator_id, "yellow"), false)) >= int(t))
            elif op == "persists":
                mark(r, run_length(level_of.get((r.indicator_id, "yellow"), false)) >= int(r.window_days))
            elif op == "before_critical":
                crit = f.get("critical_next_24h", pd.Series(0, index=idx)) == 1
                mark(r, level_of.get((m, "orange"), false) & crit)
            else:
                skipped.append(f"#{r.rule_id} {r.indicator_id}: unknown operator '{op}'")

    rows = []
    for r in rules.itertuples():
        s = hits.get(r.rule_id)
        if s is None:
            continue
        val = detail.get(r.rule_id)
        for (a, d) in s[s].index:
            if r.op in COMPARE or r.op == "flag":
                why = f"{r.metric} = {val[(a, d)]:.4g} {r.op} {r.threshold:g}" if r.op != "flag" else f"{r.metric} is set"
            elif r.op == "baseline+2sd":
                why = f"{r.metric} {val[(a, d)]:.1f} SD above personal baseline (limit {r.threshold:g} SD)"
            elif r.op == "below_baseline_by":
                why = f"{r.metric} {int(r.window_days)}-day mean {val[(a, d)]:.2f} below personal baseline (limit {r.threshold:g})"
            elif r.op == "and_yellow":
                why = f"{r.indicator_id} yellow and {r.metric} yellow on the same day"
            elif r.op == "consecutive":
                why = f"{r.indicator_id} yellow {int(r.threshold)} days in a row"
            elif r.op == "persists":
                why = f"{r.indicator_id} yellow {int(r.window_days)} days in a row"
            else:
                why = f"{r.metric} orange within 24 h of a critical event"
            rows.append({"astronaut_id": a, "time": f"{dates.get(d, '')}T00:00:00Z", "indicator_id": r.indicator_id,
                         "level": r.level, "source_engine": "rule", "rule_id": int(r.rule_id),
                         "reason": f"Day {d}: {why}", "value_ids": r.value_id})

    with con:
        con.execute("DELETE FROM alerts WHERE source_engine = 'rule'")
        if rows:
            pd.DataFrame(rows).to_sql("alerts", con, if_exists="append", index=False)
    out = pd.DataFrame(rows)
    print(f"rule alerts: {len(out):,}")
    if len(out):
        print(out.groupby(["indicator_id", "level"]).size().unstack(fill_value=0).to_string())
    for s in skipped:
        print("skipped:", s)
    con.close()


if __name__ == "__main__":
    main()
