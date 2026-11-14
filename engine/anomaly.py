
import sqlite3
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"
FEATURES = ["sleep_h_z", "work_hours_z", "pvt_lapses_z", "pvt_slowest10_ms_z", "kss_z",
            "hr_resting_z", "mood_z", "stress_z", "exercise_minutes_z"]
CONTAMINATION = 0.05
MIN_PRESENT = 6
TOP_DRIVERS = 3
SEED = 0

con = sqlite3.connect(DB, timeout=30)
f = pd.read_sql("SELECT * FROM daily_features", con).pivot_table(
    index=["astronaut_id", "mission_day"], columns="metric", values="value")
X = f[[c for c in FEATURES if c in f]]
X = X[X.notna().sum(axis=1) >= MIN_PRESENT].fillna(0)

model = IsolationForest(n_estimators=200, contamination=CONTAMINATION, random_state=SEED)
model.fit(X)

score = pd.Series(-model.decision_function(X), index=X.index)
flag = pd.Series(model.predict(X) == -1, index=X.index)

def drivers(row):
    top = row.abs().sort_values(ascending=False).head(TOP_DRIVERS)
    return ", ".join(f"{m.replace('_z', '')} {row[m]:+.1f} SD" for m in top.index)

dates = dict(pd.read_sql("SELECT mission_day, date FROM mission_timeline", con).values)
rows = [{"astronaut_id": a, "time": f"{dates.get(d, '')}T00:00:00Z", "indicator_id": None,
         "level": "yellow", "source_engine": "anomaly_model", "rule_id": None,
         "reason": f"Day {d}: unusual combination (score {score[(a, d)]:.2f}): {drivers(X.loc[(a, d)])}",
         "value_ids": None}
        for (a, d) in flag[flag].index]

with con:
    con.execute("DELETE FROM alerts WHERE source_engine = 'anomaly_model'")
    if rows:
        pd.DataFrame(rows).to_sql("alerts", con, if_exists="append", index=False)

print(f"model alerts: {len(rows)} of {len(X)} days")

lab = pd.read_sql("SELECT * FROM anomaly_labels", con)
for x in lab.itertuples():
    days = [d for (a, d) in flag[flag].index if a == x.astronaut_id and x.start_day <= d <= x.end_day]
    if days or x.scenario.startswith("3_"):
        print(x.astronaut_id, x.scenario, x.start_day, x.end_day, "-> flagged days:", days)

con.close()
