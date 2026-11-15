"""
EDA replay feed: sends real ISS cabin telemetry (OSDR EDA) to POST /environment, as the vehicle would.

It no longer computes daily values: the server does (api/env_summary.py), so replayed and live data
take the same path. This script only:
  - reads the downloaded EDA CSVs (EDA "Data Tables" tab; no API) listed in MISSIONS
  - keeps the *_ISS columns (*_Ground is the control chamber on Earth)
  - picks which real days to replay: days with >= 80 % of their readings (team design), chained onto
    mission days 1..180 in the order listed, and tags each reading with that mission_day
  - posts every reading with its real UTC time, is_real = 1

Usage (API running: uvicorn api.main:app):
  python inputs/eda.py
"""
import argparse
import os

import pandas as pd

from _feed import send

RAW = "data/raw/eda"
MISSIONS = [                                   # replay order; add more EDA missions to cover 180 days
    {"mission": "RR-1", "file": f"{RAW}/RR-1_EDA_Telemetry_data.csv"},
]
DAYS = 180
DAY_COVERAGE = 0.80                            # team design
METRIC = {"co2": ("co2_ppm", "ppm"), "temp": ("temp_c", "degC"), "rh": ("rh_pct", "%")}


def load(path):
    df = pd.read_csv(path)
    tcol = next(c for c in df.columns if c.lower().startswith("controller_time"))
    pick = {"co2": next(c for c in df.columns if c.upper().startswith("CO2") and c.upper().endswith("_ISS")),
            "temp": next(c for c in df.columns if c.lower().startswith("temp") and c.upper().endswith("_ISS")),
            "rh": next(c for c in df.columns if c.upper().startswith("RH") and c.upper().endswith("_ISS"))}
    df["time"] = pd.to_datetime(df[tcol], errors="coerce")       # Controller_Time_GMT -> UTC
    return df.dropna(subset=["time"]).drop_duplicates("time").sort_values("time"), pick


def build_rows():
    """Every EDA reading as a POST /environment row, tagged with its mission day. Returns (rows, last mission day).
    Also used by inputs/replay.py, so the replay sends exactly what this feed sends."""
    mission_day, rows = 0, []
    for m in MISSIONS:
        if not os.path.exists(m["file"]):
            print(f"missing: {m['file']} (download it from the EDA Data Tables tab)"); continue
        df, pick = load(m["file"])
        step = df["time"].diff().median()
        per_day = pd.Timedelta("1D") / step
        counts = df.groupby(df["time"].dt.date)[pick["co2"]].count()
        day_of = {}
        for d, n in counts.items():
            if n >= per_day * DAY_COVERAGE and mission_day < DAYS:
                mission_day += 1; day_of[d] = mission_day
        print(f"{m['mission']}: {df['time'].min():%Y-%m-%d} to {df['time'].max():%Y-%m-%d}, step {step}, "
              f"{len(day_of)} full days replayed, columns {list(pick.values())}")
        src = f"OSDR EDA {m['mission']}"
        for k, col in pick.items():
            metric, unit = METRIC[k]
            v = pd.to_numeric(df[col], errors="coerce")
            for t, val in zip(df["time"][v.notna()], v[v.notna()]):
                rows.append({"time": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "metric": metric,
                             "value": float(val), "unit": unit, "sensor": col, "source": src,
                             "is_real": 1, "mission_day": day_of.get(t.date())})
    return rows, mission_day


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000/environment")
    a = ap.parse_args()
    rows, mission_day = build_rows()
    if not rows:
        raise SystemExit("No EDA data to send.")
    print(f"sending {len(rows):,} readings -> {a.url}")
    print("done:", send(a.url, rows))
    print(f"mission days 1-{mission_day} of {DAYS} have real cabin data"
          + ("" if mission_day >= DAYS else " (add more EDA missions to MISSIONS for the rest)"))


if __name__ == "__main__":
    main()
