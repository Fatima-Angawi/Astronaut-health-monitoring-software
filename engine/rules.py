"""
Engine step 2: rules. Applies every enabled rule in the `rules` table (loaded from rules.json by export_kb.py)
to daily_features (written by features.py) and writes one alert per rule hit.

Operators follow the "_ops" block of rules.json exactly:
  <, >, <=, >=, ==     compare the feature with the threshold
  flag                 the feature is a 0/1 flag; fires when >= threshold (1)
  baseline+2sd         the feature's z vs personal baseline (features.py: <metric>_z) > threshold;
                       z uses the robust SD with a minimum floor, and the mean as centre for rating scales
  below_baseline_by    window mean of the feature is below the personal baseline median by >= threshold
  consecutive          this indicator's yellow on `threshold` test sessions in a row (a day with no test is skipped
                       and does not break the count; any of the indicator's yellow rules counts)
  persists             this indicator's yellow for `window_days` days in a row
  and_yellow           this indicator's yellow AND the indicator named in `metric` yellow on the same day
  before_critical      this indicator's orange with a critical event within `threshold` hours. The data is daily,
                       so hours are rounded up to whole days: 24 h = an event today or tomorrow
Composite operators run after the simple ones, and before_critical last, because they build on them.

Writes: alerts rows with source_engine = 'rule', through alert_store.sync_alerts, so a rerun keeps each alert's
id, acknowledged and synced_to_ground.
escalated_to and action are left empty: triage.py and recommendations.py fill them.
Cabin-wide rules (R03c, R21b) are written per astronaut here; triage.py merges them into one crew alert.

Usage: python engine/rules.py
"""
import math
import sqlite3
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alert_store import sync_alerts

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


def run_length_sessions(s, tested):
    """Like run_length, but counts sessions: days without a test are skipped, they do not break the run."""
    def one(x):
        t = tested.loc[x.index]
        y = x[t]
        r = y.astype(int).groupby((~y).cumsum()).cumsum()
        return r.reindex(x.index, fill_value=0)
    return s.groupby(level=0, group_keys=False).apply(one)


def main():
    con = sqlite3.connect(DB, timeout=30)
    rules = pd.read_sql("SELECT * FROM rules WHERE enabled = 1", con)
    if rules.empty:
        raise SystemExit("rules table is empty: run knowledge_base/export_kb.py first")
    f = pd.read_sql("SELECT * FROM daily_features", con)
    if f.empty:
        change = sync_alerts(con, "rule", [])
        print(f"no daily_features yet: rule alerts removed ({change['removed']})")
        con.close()
        return
    f = f.pivot_table(index=["astronaut_id", "mission_day"], columns="metric", values="value")
    base = pd.read_sql("SELECT astronaut_id, metric, median FROM baselines", con)
    med = {(r.astronaut_id, r.metric): r.median for r in base.itertuples()}
    dates = dict(pd.read_sql("SELECT mission_day, date FROM mission_timeline", con).values)
    idx = f.index
    false = pd.Series(False, index=idx)

    hits = {}                      # rule_id -> boolean Series
    level_of = {}                  # (indicator, level) -> boolean Series (any rule of that level)
    detail = {}                    # rule_id -> Series of the value that was compared (for the reason text)
    tested = {}                    # (indicator, level) -> days on which that level's rules had data (a session)
    skipped = []

    def mark(r, s, val=None):
        s = s.fillna(False).astype(bool)
        hits[r.rule_id] = s
        detail[r.rule_id] = val
        key = (r.indicator_id, r.level)
        level_of[key] = level_of.get(key, false) | s
        if val is not None:
            tested[key] = tested.get(key, false) | val.notna()

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
                key = (r.indicator_id, "yellow")              # sessions in a row: a day with no test is skipped
                mark(r, run_length_sessions(level_of.get(key, false), tested.get(key, ~false)) >= int(t))
            elif op == "persists":
                mark(r, run_length(level_of.get((r.indicator_id, "yellow"), false)) >= int(r.window_days))
            elif op == "before_critical":
                ahead = math.ceil((t if t is not None and not pd.isna(t) else 24) / 24)   # hours -> whole days (daily data)
                to_next = f.get("days_to_next_critical", pd.Series(np.nan, index=idx))
                mark(r, level_of.get((m, "orange"), false) & (to_next <= ahead))
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
                why = f"{r.indicator_id} yellow {int(r.threshold)} test sessions in a row"
            elif r.op == "persists":
                why = f"{r.indicator_id} yellow {int(r.window_days)} days in a row"
            else:
                why = f"{r.metric} orange with a critical event within {r.threshold:g} h (today or the next day)"
            rows.append({"astronaut_id": a, "time": f"{dates.get(d, '')}T00:00:00Z", "indicator_id": r.indicator_id,
                         "level": r.level, "source_engine": "rule", "rule_id": int(r.rule_id),
                         "reason": f"Day {d}: {why}", "value_ids": r.value_id})

    for x in rows:
        x.pop("source_engine")
    change = sync_alerts(con, "rule", rows)
    out = pd.DataFrame(rows)
    print(f"rule alerts: {len(out):,} ({change['kept']} kept, {change['new']} new, {change['removed']} removed)")
    if len(out):
        print(out.groupby(["indicator_id", "level"]).size().unstack(fill_value=0).to_string())
    for s in skipped:
        print("skipped:", s)
    con.close()


if __name__ == "__main__":
    main()
