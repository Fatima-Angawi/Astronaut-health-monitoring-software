"""
Runs the engine by itself after new data arrives, so results follow the data.

The write endpoints (POST /readings, /environment, /space-weather) call schedule_engine(reason) after they have
accepted at least one new row. The run starts DEBOUNCE_S seconds later; more calls in that time do not start more
runs. If a run is already going, one more run follows when it finishes, so nothing is missed.

A run executes, in order, with the same Python as the API: engine/features.py, engine/rules.py,
engine/anomaly.py, engine/triage.py, guidance/recommendations.py (each skipped if the file does not exist).
It stops at the first failure and happens in a background thread, so the POST returns at once. One run at a time.

What it records in system_state: engine_last_run (UTC ISO), engine_last_status ("ok" or the failing step and the
last lines of its output), engine_runs (count), engine_last_reason.
ENGINE_AUTORUN=0 turns it off (run_all.py does that: it runs the engine itself).
"""
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path

from api.db import connect, state_get, state_set

ROOT = Path(__file__).resolve().parents[1]
DEBOUNCE_S = 3             # TEAM DESIGN: batches of posts arrive within seconds; run once after they settle
STEPS = ["engine/features.py", "engine/rules.py", "engine/anomaly.py", "engine/triage.py",
         "guidance/recommendations.py"]
TAIL_LINES = 5             # TEAM DESIGN: lines of a failing step's output kept in engine_last_status

_lock = threading.Lock()
_timer = None              # a run is waiting for its debounce
_running = False
_again = False             # a call came in during a run: run once more when it ends
_reason = "start"


def enabled():
    return os.environ.get("ENGINE_AUTORUN", "1") != "0"


def _start_timer():
    global _timer
    _timer = threading.Timer(DEBOUNCE_S, _run)
    _timer.daemon = True
    _timer.start()


def schedule_engine(reason):
    """Ask for an engine run soon. Cheap and safe to call on every accepted write."""
    global _again, _reason
    if not enabled():
        return
    with _lock:
        _reason = reason
        if _running:
            _again = True
        elif _timer is None:
            _start_timer()


def _run():
    global _timer, _running, _again
    with _lock:
        _timer, _running, _again = None, True, False
        reason = _reason
    status = "ok"
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        for step in STEPS:
            if not (ROOT / step).exists():
                continue
            r = subprocess.run([sys.executable, step], cwd=ROOT, env=env, capture_output=True,
                               text=True, encoding="utf-8", errors="replace")
            if r.returncode != 0:
                tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-TAIL_LINES:])
                status = f"failed at {step}: {tail}"
                break
    except Exception as e:                                 # never let the thread die silently
        status = f"failed to run the engine: {e}"
    try:
        con = connect()
        with con:
            n = int(state_get(con, "engine_runs", "0")) + 1
            state_set(con, engine_last_run=datetime.now(timezone.utc).isoformat(), engine_last_status=status,
                      engine_runs=n, engine_last_reason=reason)
        con.close()
    finally:
        with _lock:
            _running = False
            if _again:
                _again = False
                _start_timer()
