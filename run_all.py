"""
Run the whole project, or only some stages, in the right order.

  python run_all.py                  all stages: db, crew, real, dose, engine, test
  python run_all.py engine           only the engine (after changing rules.json or engine code)
  python run_all.py crew engine      several stages, always run in pipeline order
  python run_all.py --list           show the stages and their steps

Stages:
  db      reset the database, load the knowledge base and rules
  crew    simulator, bone, behavior generators; load the mission setup; send crew data
  real    RadLab, DONKI, EDA replays (RadLab takes about 10 minutes)
  dose    personal dose (needs the RadLab data from "real")
  engine  features, rules, anomaly, triage, recommendations (the last three are skipped if their files do not exist)
  test    compare the alerts with the injected scenarios (test_scenarios.py)

The script starts the API itself when a stage needs it and stops it at the end, so the database is never
locked during a reset. If an API is already running (e.g. you started uvicorn yourself), it is used as is,
but the "db" stage refuses to run, because the reset cannot delete a database the server holds open.

Note: re-sent rows are skipped as duplicates, so after changing a generator's values run from "db"
(python run_all.py), not just the generator's stage.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
API = "http://127.0.0.1:8000"
PY = sys.executable

STAGES = {
    "db":     ["db/init_db.py --reset", "knowledge_base/export_kb.py"],
    "crew":   ["inputs/simulator.py", "inputs/generate_bone.py", "inputs/generate_behavior.py",
               "inputs/load_db.py", "inputs/send_virtual.py"],
    "real":   ["inputs/send_radlab.py", "inputs/donki.py", "inputs/send_donki.py", "inputs/eda.py"],
    "dose":   ["inputs/generate_dose.py", "inputs/send_virtual.py", "inputs/load_db.py"],
    "engine": ["engine/features.py", "engine/rules.py", "engine/anomaly.py", "engine/triage.py",
               "guidance/recommendations.py"],
    "test":   ["test_scenarios.py"],
}
ORDER = list(STAGES)
NEEDS_API = {"crew", "real", "dose"}
OPTIONAL = {"inputs/eda.py", "inputs/donki.py", "engine/anomaly.py", "engine/triage.py", "guidance/recommendations.py"}   # a failure here warns, does not stop
GENERATED = ["sim_readings.csv", "behavior_readings.csv", "behavior_truth.csv", "bone_readings.csv",
             "bone_truth.csv", "bone_preflight.csv", "bone_anomaly_labels.csv", "anomaly_labels.csv",
             "dose_readings.csv", "dose_anomaly_labels.csv"]


def api_up():
    try:
        return requests.get(f"{API}/docs", timeout=2).ok
    except requests.RequestException:
        return False


def start_api():
    p = subprocess.Popen([PY, "-m", "uvicorn", "api.main:app", "--port", "8000"], cwd=ROOT,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(30):
        if api_up():
            print("   API started")
            return p
        time.sleep(1)
    p.terminate()
    sys.exit("API did not start: run 'uvicorn api.main:app' yourself to see the error.")


def run(step, env):
    script, *args = step.split()
    if not (ROOT / script).exists():
        if script in OPTIONAL:
            print(f"-- skip {script} (not found)"); return
        sys.exit(f"missing {script}")
    print(f"\n== {step}")
    t = time.time()
    r = subprocess.run([PY, script, *args], cwd=ROOT, env=env)
    if r.returncode != 0:
        if script in OPTIONAL:
            print(f"!! {script} failed (optional, continuing)"); return
        sys.exit(f"\nSTOPPED: {step} failed (exit {r.returncode}). Fix it, then rerun from this stage.")
    print(f"   done in {time.time() - t:.0f}s")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--list" in sys.argv:
        for s in ORDER:
            print(f"{s:7} " + " | ".join(STAGES[s]))
        return
    unknown = [a for a in args if a not in STAGES]
    if unknown:
        sys.exit(f"unknown stage(s) {unknown}; choose from {ORDER}")
    stages = [s for s in ORDER if s in args] or ORDER
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    already_up = api_up()
    if "db" in stages and already_up:
        sys.exit("An API server is running and holds the database open. Stop it (Ctrl+C in its terminal), "
                 "then run again: this script starts its own.")
    if "crew" in stages:                                   # no stale generated file can be sent by mistake
        for f in GENERATED:
            (ROOT / "data" / "generated" / f).unlink(missing_ok=True)

    server, t0 = None, time.time()
    try:
        for s in stages:
            print(f"\n######## stage: {s}")
            if s in NEEDS_API and not api_up():
                server = start_api()
            for step in STAGES[s]:
                run(step, env)
    finally:
        if server:
            server.terminate(); server.wait()
            print("\n   API stopped")
    print(f"\nAll done: {', '.join(stages)} in {(time.time() - t0) / 60:.1f} min")


if __name__ == "__main__":
    main()
