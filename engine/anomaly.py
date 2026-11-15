"""
Engine step 3: anomaly model. Flags astronaut-days whose COMBINATION of measures is unusual, even when no
single rule fires (e.g. normal reported mood while PVT worsens and sleep is short).

Method (TEAM DESIGN; no NASA source prescribes it):
  - Inputs: each astronaut's daily z-scores against their own baseline (features.py), so the crew share one scale.
  - Training: an Isolation Forest fitted ONLY on the baseline period (mission days 1-14, all crew together).
    A live system has nothing else to learn from, and later days never change the model.
  - Alerting: a day is flagged when its score is more unusual than every baseline day by MARGIN.
    The cut-off is fixed after training, so the number of flagged days follows the data: a quiet mission
    gives few alerts, a bad one many (no fixed share of days is flagged).
  - Each alert names the measures furthest from baseline. Alerts are yellow; triage.py decides what they mean.
  - Baseline days are never flagged (the model was trained on them).

Writes alerts with source_engine = 'anomaly_model' through alert_store.sync_alerts (acknowledged state is kept).
Never reads anomaly_labels or truth files.
Usage: python engine/anomaly.py
"""
import sqlite3
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import IsolationForest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from alert_store import sync_alerts

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"
FEATURES = ["sleep_h_z", "work_hours_z", "pvt_lapses_z", "pvt_slowest10_ms_z", "kss_z",
            "hr_resting_z", "mood_z", "stress_z", "exercise_minutes_z"]
TRAIN_DAYS = (1, 14)      # same baseline period as features.py
MARGIN = 0.04             # TEAM DESIGN: how far beyond the most unusual baseline day a score must be
MIN_TRAIN = 20            # TEAM DESIGN: fewest baseline astronaut-days the model is trained on
MIN_PRESENT = 6           # TEAM DESIGN: skip days with fewer than 6 of the 9 inputs
TOP_DRIVERS = 3
SEED = 0


def main():
    con = sqlite3.connect(DB, timeout=30)
    def wait():
        sync_alerts(con, "anomaly_model", [])
        print("model waits for the baseline period (days 1-14)")
        con.close()

    f = pd.read_sql("SELECT * FROM daily_features", con)
    if f.empty:
        return wait()
    f = f.pivot_table(index=["astronaut_id", "mission_day"], columns="metric", values="value")
    X = f[[c for c in FEATURES if c in f]]
    X = X[X.notna().sum(axis=1) >= MIN_PRESENT].fillna(0)             # a missing input = "at baseline"
    day = X.index.get_level_values("mission_day")
    train = X[(day >= TRAIN_DAYS[0]) & (day <= TRAIN_DAYS[1])]
    if len(train) < MIN_TRAIN:
        return wait()

    model = IsolationForest(n_estimators=300, random_state=SEED).fit(train)
    score = pd.Series(-model.score_samples(X), index=X.index)          # higher = more unusual
    cutoff = score[train.index].max() + MARGIN
    live = X[day > TRAIN_DAYS[1]]
    flagged = score[live.index][score[live.index] > cutoff]

    dates = dict(pd.read_sql("SELECT mission_day, date FROM mission_timeline", con).values)
    def drivers(row):
        top = row.abs().sort_values(ascending=False).head(TOP_DRIVERS)
        return ", ".join(f"{m.replace('_z', '')} {row[m]:+.1f} SD" for m in top.index)
    rows = [{"astronaut_id": a, "time": f"{dates.get(d, '')}T00:00:00Z", "indicator_id": None, "level": "yellow",
             "rule_id": None, "value_ids": None,
             "reason": f"Day {d}: unusual combination (score {s:.2f}, cut-off {cutoff:.2f}): {drivers(X.loc[(a, d)])}"}
            for (a, d), s in flagged.items()]
    change = sync_alerts(con, "anomaly_model", rows)
    print(f"model: trained on {len(train)} baseline days, cut-off {cutoff:.3f}; "
          f"flagged {len(rows)} of {len(live)} later days ({change['kept']} kept, {change['new']} new, {change['removed']} removed)")
    if len(flagged):
        print(flagged.groupby(level=0).size().to_string())
    con.close()


if __name__ == "__main__":
    main()
