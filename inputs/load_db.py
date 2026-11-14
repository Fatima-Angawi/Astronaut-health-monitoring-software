"""
Loads the mission SETUP (not measurements) into health.db: crew, mission_timeline, mission_events, anomaly_labels.
Reads data/generated/*.csv written by simulator.py. Only columns that exist in the table are loaded:
the simulator's hidden per-person parameters (sleep_mean_h, hr_mean_bpm, ...) are its ground truth for testing,
not facts the system may know, so they are NOT loaded. Re-running replaces these four tables.
Run before any feed: /readings rejects everything while crew is empty.
Usage: python inputs/load_db.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "health.db"
GEN = ROOT / "data" / "generated"
TABLES = ["crew", "mission_timeline", "mission_events"]
ABMD = ["preflight_abmd_total_hip", "preflight_abmd_lumbar_spine", "preflight_abmd_femoral_neck"]


def load(con, table, f):
    df = pd.read_csv(f)
    cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
    keep = [c for c in df.columns if c in cols]
    skipped = [c for c in df.columns if c not in cols]
    df[keep].to_sql(table, con, if_exists="append", index=False)
    print(f"{table} <- {f.name}: {len(df)} rows, loaded {keep}" + (f"; not loaded: {skipped}" if skipped else ""))


def main():
    with sqlite3.connect(DB, timeout=30) as con:
        for t in TABLES:
            f = GEN / f"{t}.csv"
            if not f.exists():
                print(f"missing {f}: run inputs/simulator.py first"); continue
            con.execute(f"DELETE FROM {t}")
            load(con, t, f)

        # preflight DXA per site (bone generator); bone_truth.csv / behavior_truth.csv are never loaded
        pre = GEN / "bone_preflight.csv"
        if pre.exists():
            df = pd.read_csv(pre)
            for r in df.itertuples(index=False):
                con.execute(f"UPDATE crew SET {', '.join(c + '=?' for c in ABMD)} WHERE astronaut_id=?",
                            (*[float(getattr(r, c)) for c in ABMD], r.astronaut_id))
            print(f"crew <- {pre.name}: preflight aBMD set for {len(df)} astronauts")
        else:
            print(f"missing {pre}: crew preflight aBMD left empty (run inputs/generate_bone.py)")

        # every label file: anomaly_labels.csv (simulator + behavior), bone_anomaly_labels.csv, ...
        con.execute("DELETE FROM anomaly_labels")
        for f in sorted(GEN.glob("*anomaly_labels*.csv")):
            load(con, "anomaly_labels", f)


if __name__ == "__main__":
    main()
