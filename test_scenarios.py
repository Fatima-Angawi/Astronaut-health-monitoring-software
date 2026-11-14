"""
Validation: compares the engine's alerts with the injected scenarios (anomaly_labels).
This is the ONLY script that reads anomaly_labels; the engine never does.

Prints five parts:
  1. Scenarios        caught / missed, the first day caught and the delay from the scenario's first day
  2. Decoys           quiet / yellow only (acceptable) / false alarm (orange or red)
  3. Not scored       labels with expected level model_only, pvt_only, linked, context: what fired
  4. Outside labels   rule alert days that match no label, per indicator and level
  5. Anomaly model    precision and recall per astronaut-day, and per scenario

Scoring choices (TEAM DESIGN):
  - A scenario is caught if the same astronaut has an alert of the same indicator, at the expected level or
    higher, on a day inside the label.
  - A decoy day with only a yellow is acceptable (several yellow rules fire on a single day by definition);
    an orange or red on a decoy is a false alarm.
  - TAIL_DAYS: rules that use a 7-day window stay true for up to 6 days after the cause ends, so alert days
    up to 6 days after a label are counted as "tail", not as outside.
  - Alerts driven by real NASA data carry no label and are listed separately as "real data":
    cabin CO2 (R03c) on days that have real EDA data, and all SPE alerts (R21b, from DONKI).
  - Model truth: astronaut-days inside a non-decoy label of an indicator the model can see (MODEL_INDICATORS).
    With 4 astronauts and 180 days these figures illustrate the method; they do not validate it.

Usage (after the engine has run):  python test_scenarios.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).resolve().parent / "data" / "health.db"
RANK = {"yellow": 1, "orange": 2, "red": 3}
TAIL_DAYS = 6
REAL_INDICATORS = {"R21b"}                                             # driven by real DONKI events: no labels
MODEL_INDICATORS = {"R01", "R01c", "R01d", "R01f", "R10b", "R02e"}     # what the model's inputs can show
MODEL_TRUTH_LEVELS = set(RANK) | {"model_only"}


def main():
    con = sqlite3.connect(DB, timeout=30)
    day_of = dict(pd.read_sql("SELECT date, mission_day FROM mission_timeline", con).values)
    al = pd.read_sql("SELECT astronaut_id, time, indicator_id, level, source_engine FROM alerts", con)
    lab = pd.read_sql("SELECT * FROM anomaly_labels", con)
    real_co2_days = set(pd.read_sql("SELECT DISTINCT mission_day FROM env_daily WHERE is_real = 1 "
                                    "AND metric = 'co2_1h_max_mmhg' AND mission_day IS NOT NULL", con).mission_day)
    con.close()
    if al.empty or lab.empty:
        raise SystemExit("alerts or anomaly_labels is empty: run the engine and inputs/load_db.py first")
    al["day"] = al.time.str[:10].map(day_of)
    al = al.dropna(subset=["day"]); al["day"] = al.day.astype(int)
    al["rank"] = al.level.map(RANK)
    rules, model = al[al.source_engine == "rule"], al[al.source_engine == "anomaly_model"]
    model_days = set(zip(model.astronaut_id, model.day))

    def fired(x, src=rules):
        return src[(src.astronaut_id == x.astronaut_id) & (src.indicator_id == x.indicator_id)
                   & (src.day >= x.start_day) & (src.day <= x.end_day)]

    # ---- 1. scenarios
    scored = lab[(lab.is_decoy == 0) & lab.expected_level.isin(RANK)]
    print(f"1. SCENARIOS ({len(scored)})")
    caught = 0
    for x in scored.itertuples():
        a = fired(x)
        ok = a[a["rank"] >= RANK[x.expected_level]]
        if len(ok):
            caught += 1
            first = int(ok.day.min())
            note = f"caught day {first} (+{first - x.start_day} d)"
        else:
            note = "MISSED" + (f" (highest: {a.sort_values('rank').level.iloc[-1]})" if len(a) else " (nothing fired)")
        if not len(ok):
            print(f"   {x.astronaut_id} {x.indicator_id:5} {x.scenario:36} days {x.start_day}-{x.end_day} {x.expected_level:7} {note}")
    print(f"   caught {caught} of {len(scored)}" + ("" if caught < len(scored) else " (all)"))
    delays = [int(fired(x)[fired(x)["rank"] >= RANK[x.expected_level]].day.min()) - x.start_day
              for x in scored.itertuples() if len(fired(x)[fired(x)["rank"] >= RANK[x.expected_level]])]
    if delays:
        print(f"   delay from scenario start: median {pd.Series(delays).median():.0f} d, max {max(delays)} d")

    # ---- 2. decoys
    decoys = lab[lab.is_decoy == 1]
    quiet = yellow = 0
    print(f"\n2. DECOYS ({len(decoys)})")
    for x in decoys.itertuples():
        a = fired(x)
        top = a["rank"].max() if len(a) else 0
        if top == 0:
            quiet += 1
        elif top == 1:
            yellow += 1
        else:
            print(f"   FALSE ALARM {x.astronaut_id} {x.indicator_id} {x.scenario} day {x.start_day}: "
                  f"{sorted(a.level.unique(), key=RANK.get)}")
    print(f"   quiet {quiet}, yellow only {yellow}, false alarms {len(decoys) - quiet - yellow}")

    # ---- 3. not scored
    other = lab[(lab.is_decoy == 0) & ~lab.expected_level.isin(RANK)]
    print(f"\n3. NOT SCORED ({len(other)})")
    for x in other.itertuples():
        a = fired(x)
        m = sorted(d for (p, d) in model_days if p == x.astronaut_id and x.start_day <= d <= x.end_day)
        what = ", ".join(f"{l} from day {int(a[a.level == l].day.min())}" for l in RANK if (a.level == l).any()) or "no rule alert"
        print(f"   {x.astronaut_id} {x.indicator_id:5} {x.scenario:28} days {x.start_day}-{x.end_day} ({x.expected_level}): "
              f"{what}; model flagged {len(m)} day(s)")

    # ---- 4. rule alerts outside labels
    windows = {}
    for x in lab.itertuples():
        windows.setdefault((x.astronaut_id, x.indicator_id), []).append((x.start_day, x.end_day))
    def where(r):
        if r.indicator_id in REAL_INDICATORS or (r.indicator_id == "R03c" and r.day in real_co2_days):
            return "real data"
        w = windows.get((r.astronaut_id, r.indicator_id), [])
        if any(s <= r.day <= e for s, e in w):
            return "in label"
        if any(e < r.day <= e + TAIL_DAYS for s, e in w):
            return "tail"
        return "outside"
    rd = rules.drop_duplicates(["astronaut_id", "indicator_id", "level", "day"]).copy()
    rd["where"] = [where(r) for r in rd.itertuples()]
    print("\n4. RULE ALERT DAYS BY PLACE (astronaut-days)")
    print(rd.groupby(["indicator_id", "level", "where"]).size().unstack(fill_value=0)
            .reindex(columns=["in label", "tail", "outside", "real data"], fill_value=0).to_string())

    # ---- 5. anomaly model
    print("\n5. ANOMALY MODEL")
    if model.empty:
        print("   no model alerts (engine/anomaly.py not run)")
        return
    truth_lab = lab[(lab.is_decoy == 0) & lab.indicator_id.isin(MODEL_INDICATORS) & lab.expected_level.isin(MODEL_TRUTH_LEVELS)]
    truth = {(x.astronaut_id, d) for x in truth_lab.itertuples() for d in range(x.start_day, x.end_day + 1)}
    decoy_days = {(x.astronaut_id, x.start_day) for x in decoys.itertuples()}
    tp = len(model_days & truth)
    print(f"   flagged astronaut-days: {len(model_days)} | scenario astronaut-days: {len(truth)}")
    print(f"   precision {tp / len(model_days):.2f} ({tp} of {len(model_days)} flagged days are inside a scenario)")
    print(f"   recall    {tp / len(truth):.2f} ({tp} of {len(truth)} scenario days flagged)")
    hit = sum(any((x.astronaut_id, d) in model_days for d in range(x.start_day, x.end_day + 1)) for x in truth_lab.itertuples())
    print(f"   scenarios with at least one flagged day: {hit} of {len(truth_lab)}")
    print(f"   decoy days flagged: {len(model_days & decoy_days)} of {len(decoy_days)}")
    for x in lab[lab.expected_level == "model_only"].itertuples():
        m = sorted(d for (p, d) in model_days if p == x.astronaut_id and x.start_day <= d <= x.end_day)
        print(f"   model-only scenario {x.astronaut_id} {x.scenario} days {x.start_day}-{x.end_day}: flagged days {m}")


if __name__ == "__main__":
    main()
