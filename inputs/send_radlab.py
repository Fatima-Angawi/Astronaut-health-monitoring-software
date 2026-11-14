"""
RadLab replay feed: sends downloaded ISS area-dose files to POST /environment, as an onboard detector would.

Reads data/raw/radlab/*.csv (the files saved from the RadLab API: timestamp, instrument_id,
absorbed_dose_rate [uGy/h], dose_equivalent_rate [uSv/h, ALTEA only], l, latitude, longitude).
RadLab timestamps carry no zone; they are UTC, so "Z" is added here.
Unzip the RadLab downloads so the CSVs sit directly in data/raw/radlab/ (no subfolders).

Replay (team design): DosTel1 2024 is the mission replay, day 1 = 2024-01-01, so the
12 Feb 2024 SPE lands on mission day 43. Other instruments/years (ALTEA 2010–2012) are sent
with no mission_day: stored and summarised for analysis, but not part of the mission timeline.
The server integrates the rates into daily dose (api/env_summary.py).

Fetching from RadLab stays in radlab.py; this script only sends what is on disk.

Usage (API running):  python inputs/send_radlab.py
"""
import argparse
import glob

import pandas as pd

from _feed import send

REPLAY_START = {"DosTel1": "2024-01-01"}       # instrument -> real date of mission day 1; team design: day 43 = 12 Feb 2024 SPE
DAYS = 180                                     # mission length (team design)


def rows_from(path):
    df = pd.read_csv(path)
    out = []
    for r in df.itertuples(index=False):
        t = pd.Timestamp(r.timestamp)
        start = REPLAY_START.get(r.instrument_id)
        md = (t.normalize() - pd.Timestamp(start)).days + 1 if start else None
        md = md if md and 1 <= md <= DAYS else None
        base = {"time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "sensor": r.instrument_id, "source": f"RadLab {r.instrument_id}",
                "is_real": 1, "mission_day": md, "latitude": float(r.latitude),
                "longitude": float(r.longitude), "l_value": float(r.l)}
        if pd.notna(r.absorbed_dose_rate):
            out.append({**base, "metric": "absorbed_dose_rate_uGy_h", "value": float(r.absorbed_dose_rate), "unit": "uGy/h"})
        if "dose_equivalent_rate" in df.columns and pd.notna(r.dose_equivalent_rate):
            out.append({**base, "metric": "dose_eq_rate_uSv_h", "value": float(r.dose_equivalent_rate), "unit": "uSv/h"})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/environment")
    ap.add_argument("--folder", default="data/raw/radlab")
    a = ap.parse_args()
    rows = []
    for p in sorted(glob.glob(f"{a.folder}/*.csv")):
        r = rows_from(p); rows += r; print(f"{p}: {len(r):,} readings")
    if not rows:
        raise SystemExit(f"No RadLab files in {a.folder}")
    print("done:", send(a.url, rows))


if __name__ == "__main__":
    main()
