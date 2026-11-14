"""
Virtual device: sends the generated crew data to the API exactly as real hardware would.

Reads every data/generated/*readings*.csv (simulator, behavior, bone…) and POSTs it to
/readings in batches, with device = the file's source column (e.g. "simulator") and is_real = 0.
The database is filled only through the API, so the path from device to alert is the same
for simulated and real data.

Usage (API running: uvicorn api.main:app):
  python inputs/send_virtual.py
  python inputs/send_virtual.py --url http://localhost:8000/readings --batch 500
"""
import argparse
import glob
import os

import pandas as pd

from _feed import send

READING_TIME = "T07:00:00Z"      # generated rows have a date only: one fixed morning time (team design)


def rows_from(path):
    df = pd.read_csv(path)
    need = {"astronaut_id", "date", "mission_day", "metric", "value", "unit"}
    if not need <= set(df.columns):
        print(f"skip {path}: missing {need - set(df.columns)}"); return []
    return [{
        "astronaut_id": r.astronaut_id,
        "metric": r.metric,
        "value": float(r.value),
        "unit": r.unit,
        "time": f"{r.date}{READING_TIME}",
        "device": getattr(r, "source", "simulator"),
        "is_real": int(getattr(r, "is_real", 0)),
        "mission_day": int(r.mission_day),
        "availability": getattr(r, "availability", "live"),
    } for r in df.itertuples(index=False)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/readings")
    ap.add_argument("--batch", type=int, default=500)
    ap.add_argument("--folder", default="data/generated")
    a = ap.parse_args()

    totals = {"accepted": 0, "duplicates": 0, "rejected": 0}
    for path in sorted(glob.glob(f"{a.folder}/*readings*.csv")):
        if "truth" in os.path.basename(path):          # answer keys (bone_truth, behavior_truth) are never sent
            print(f"skip {path}: truth file"); continue
        rows = rows_from(path)
        print(f"{path}: {len(rows):,} readings")
        r = send(a.url, rows, batch=a.batch)
        for k in totals:
            totals[k] += r.get(k, 0)
    print(f"done: {totals}")


if __name__ == "__main__":
    main()
