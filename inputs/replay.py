"""
Replay: plays the simulated mission back one day at a time, following the mission clock, through the same
endpoints a real feed would use (POST /readings, /environment, /space-weather).

Two steps:

  python inputs/replay.py --prepare      (API stopped)
      Needs the files a full run leaves behind: data/generated/*.csv (incl. dose_readings.csv) and the raw files
      data/raw/radlab/, data/raw/eda/, data/raw/donki/SPE_events.json. If they are missing: run python run_all.py first.
      Builds data/replay/day_NNN.json (one file per mission day with three lists: readings, environment,
      space_weather) and resets the database to an empty mission (db/init_db.py --reset, export_kb.py, load_db.py).
      The mission clock starts at day 0, paused.

  python inputs/replay.py                (API running)
      Every POLL_S seconds reads GET /mission. For each day from replay_sent_through + 1 up to current_day it posts
      that day's three lists, then records the day with POST /mission/clock {"action": "replay_progress"}.
      Ctrl+C stops it cleanly; running it again continues where it stopped. It never runs the engine: the API does,
      after the data arrives (api/engine_runner.py).

What is in a day's file (built with the row code of the existing feeds, imported, not copied):
  readings       all data/generated/*readings*.csv rows except *truth*, for that mission day
                 (preflight rows, mission day < 1, go with day 1; after_return rows go with the last day)
  environment    EDA raw readings (inputs/eda.py) and RadLab DosTel1 readings (inputs/send_radlab.py);
                 ALTEA has no mission day and is not replayed; EDA readings that belong to no full day go with the
                 first or the last EDA day, so the 1-hour CO2 window at the edges sees the same data as a batch run
  space_weather  DONKI records whose onset date maps to that day through mission_timeline.replay_date
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
os.chdir(ROOT)                                   # the feeds use project-relative paths

import eda                                       # noqa: E402  (row code of the existing feeds)
import send_donki                                # noqa: E402
import send_radlab                               # noqa: E402
import send_virtual                              # noqa: E402
from _feed import send                           # noqa: E402

REPLAY_DIR = ROOT / "data" / "replay"
GEN = ROOT / "data" / "generated"
DONKI = ROOT / "data" / "raw" / "donki" / "SPE_events.json"
EDA_FILE = ROOT / "data" / "raw" / "eda" / "RR-1_EDA_Telemetry_data.csv"
RADLAB_DIR = ROOT / "data" / "raw" / "radlab"
POLL_S = 2                                       # TEAM DESIGN: how often the clock is read
READINGS_BATCH, ENV_BATCH, SPE_BATCH = 500, 5000, 500   # same as send_virtual.py, eda.py / send_radlab.py, send_donki.py


# ------------------------------------------------------------------ prepare
def readings_files():
    return [p for p in sorted(GEN.glob("*readings*.csv")) if "truth" not in p.name]


def radlab_files():
    """RadLab files of the replayed instruments whose month falls inside the mission window."""
    out = []
    for inst, start in send_radlab.REPLAY_START.items():
        first = date.fromisoformat(start)
        months = {(first + timedelta(days=i)).strftime("%Y-%m") for i in range(send_radlab.DAYS)}
        out += [p for p in sorted(RADLAB_DIR.glob(f"{inst.lower()}_*.csv")) if p.stem[-7:] in months]
    return out


def stop(msg):
    sys.exit(msg)


def prepare(api):
    missing = [str(p) for p in [GEN / "mission_timeline.csv", GEN / "dose_readings.csv", GEN / "sim_readings.csv",
                                EDA_FILE, DONKI] if not p.exists()]
    if not radlab_files():
        missing.append(f"{RADLAB_DIR}/dostel1_*.csv")
    if missing:
        stop("Missing: " + ", ".join(missing) + "\nRun python run_all.py first (and put the raw files in data/raw/).")
    try:
        if requests.get(f"{api}/docs", timeout=2).ok:
            stop("The API is running and holds the database open. Stop it, then run --prepare again.")
    except requests.RequestException:
        pass

    tl = pd.read_csv(GEN / "mission_timeline.csv")
    days = [int(d) for d in tl.mission_day]
    last = days[-1]
    day_of_replay = dict(zip(tl.replay_date, tl.mission_day))
    plan = {d: {"mission_day": d, "readings": [], "environment": [], "space_weather": []} for d in days}

    for path in readings_files():
        for r in send_virtual.rows_from(str(path)):
            d = last if r["availability"] == "after_return" else min(max(int(r["mission_day"]), 1), last)
            plan[d]["readings"].append(r)

    eda_rows, _ = eda.build_rows()
    mapped = [r for r in eda_rows if r["mission_day"]]
    first_time, last_eda_day = min(r["time"] for r in mapped), max(r["mission_day"] for r in mapped)
    for r in eda_rows:
        d = r["mission_day"] or (1 if r["time"] < first_time else last_eda_day)
        plan[min(d, last)]["environment"].append(r)
    for path in radlab_files():
        for r in send_radlab.rows_from(str(path)):
            if r["mission_day"]:
                plan[min(r["mission_day"], last)]["environment"].append(r)

    for rec in send_donki.records(json.load(open(DONKI, encoding="utf-8"))):
        d = day_of_replay.get(str(rec["eventTime"])[:10])
        if d is not None:
            plan[int(d)]["space_weather"].append(rec)

    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    for old in REPLAY_DIR.glob("day_*.json"):
        old.unlink()
    for d, content in plan.items():
        (REPLAY_DIR / f"day_{d:03d}.json").write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
    n = lambda k: sum(len(c[k]) for c in plan.values())
    print(f"data/replay: {len(plan)} day files | readings {n('readings'):,}, environment {n('environment'):,}, "
          f"space-weather {n('space_weather')}")

    # empty mission: the schema starts the clock at day 0, paused
    for f in (ROOT / "data" / "health.db-wal", ROOT / "data" / "health.db-shm"):
        f.unlink(missing_ok=True)
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    for step in (["db/init_db.py", "--reset"], ["knowledge_base/export_kb.py"], ["inputs/load_db.py"]):
        r = subprocess.run([sys.executable, *step], cwd=ROOT, env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode != 0:
            stop(f"{' '.join(step)} failed:\n{r.stdout}{r.stderr}")
    print("database reset to an empty mission; clock at day 0, paused. Start the API, then run "
          "python inputs/replay.py and start the clock.")


# ------------------------------------------------------------------ follow the clock
def send_day(api, day):
    """Post one day's three lists. Returns a short summary, or None if the day's file is missing."""
    f = REPLAY_DIR / f"day_{day:03d}.json"
    if not f.exists():
        return None
    content = json.loads(f.read_text(encoding="utf-8"))
    out = []
    for key, path, batch in (("readings", "/readings", READINGS_BATCH), ("environment", "/environment", ENV_BATCH),
                             ("space_weather", "/space-weather", SPE_BATCH)):
        rows = content[key]
        if rows:
            tot = send(api + path, rows, batch=batch)
            out.append(f"{key} {len(rows)} ({tot.get('rejected', 0)} rejected)")
        else:
            out.append(f"{key} 0")
    return ", ".join(out)


def follow(api):
    print(f"replay follows the mission clock at {api} (Ctrl+C to stop)")
    waiting = False
    try:
        while True:
            try:
                m = requests.get(f"{api}/mission", timeout=10).json()
                ok = m.get("ok")
            except (requests.RequestException, ValueError):
                ok = False
            if not ok:
                if not waiting:
                    print("waiting for the API ...")
                waiting = True
                time.sleep(POLL_S)
                continue
            waiting = False
            for d in range(m["replay_sent_through"] + 1, m["current_day"] + 1):
                try:
                    summary = send_day(api, d)
                except SystemExit as e:                  # API refused or went away: try this day again next time
                    print(f"day {d}: {e}")
                    break
                if summary is None:
                    print(f"day {d}: no file in data/replay; run python inputs/replay.py --prepare")
                    break
                requests.post(f"{api}/mission/clock", json={"action": "replay_progress", "day": d}, timeout=10)
                print(f"day {d:3}: {summary}")
            time.sleep(POLL_S)
    except KeyboardInterrupt:
        print("\nreplay stopped; it continues from the last sent day when started again")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare", action="store_true", help="build data/replay and reset the database (API stopped)")
    ap.add_argument("--api", default=os.environ.get("API_URL", "http://127.0.0.1:8000"))
    a = ap.parse_args()
    prepare(a.api) if a.prepare else follow(a.api)


if __name__ == "__main__":
    main()
