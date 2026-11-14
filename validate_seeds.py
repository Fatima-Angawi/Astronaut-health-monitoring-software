"""
Robustness check: runs the simulated part of the pipeline with several random seeds and reports, per seed,
how many scenarios were caught and how many decoys raised a false alarm.

Why: the scenarios and the thresholds were designed by the same team on one random draw (the default seeds).
If "caught N of N" holds only for that draw, the thresholds are tuned to it. This script shows the spread.

How: for each seed offset it copies the project (without data/) to a temporary folder and runs
  python run_all.py db crew engine test
there with SIM_SEED_OFFSET set, so the real database is never touched. The real-data stages (RadLab, DONKI,
EDA) and the dose stage are skipped: they do not depend on the seed. Offset 0 = the default seeds.

Usage:  python validate_seeds.py            (offsets 0-4)
        python validate_seeds.py 10         (offsets 0-9)
Stop any running API server first (each run starts its own on port 8000).
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5


def main():
    results = []
    for off in range(N):
        tmp = Path(tempfile.mkdtemp(prefix=f"seed{off}_"))
        work = tmp / "project"
        shutil.copytree(ROOT, work, ignore=shutil.ignore_patterns("data", ".git", "__pycache__", "*.zip", ".venv", "venv"))
        (work / "data").mkdir()
        env = {**os.environ, "SIM_SEED_OFFSET": str(off), "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run([sys.executable, "run_all.py", "db", "crew", "engine", "test"], cwd=work, env=env,
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = r.stdout + r.stderr
        row = {"offset": off, "ok": r.returncode == 0}
        m = re.search(r"caught (\d+) of (\d+)", out)
        row["caught"] = f"{m.group(1)}/{m.group(2)}" if m else "?"
        row["missed"] = "; ".join(" ".join(l.split()[:3]) for l in out.splitlines() if "MISSED" in l)
        m = re.search(r"quiet (\d+), yellow only (\d+), false alarms (\d+)", out)
        row["false_alarms"] = m.group(3) if m else "?"
        m = re.search(r"precision ([\d.]+)", out); row["precision"] = m.group(1) if m else "-"
        m = re.search(r"recall\s+([\d.]+)", out);  row["recall"] = m.group(1) if m else "-"
        m = re.search(r"model-only scenario .*flagged days \[(.*)\]", out)
        row["underreporting_days_flagged"] = len([x for x in m.group(1).split(",") if x.strip()]) if m else "-"
        results.append(row)
        if r.returncode != 0:
            (ROOT / f"validate_seed_{off}.log").write_text(out, encoding="utf-8")
            print(f"offset {off}: FAILED, log saved to validate_seed_{off}.log")
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"offset {off}: caught {row['caught']}, decoy false alarms {row['false_alarms']}, "
              f"model precision {row['precision']} recall {row['recall']}, "
              f"underreporting days flagged {row['underreporting_days_flagged']}"
              + (f" | missed: {row['missed']}" if row["missed"] else ""))
    full = sum(r["ok"] and all("R02c" in m for m in r["missed"].split("; ") if m) for r in results)
    print(f"\n{N} seeds: every scenario that has a rule was caught in {full} of {N}; "
          f"decoy false alarms per seed: {[r['false_alarms'] for r in results]}")
    print("R02c (countermeasure gap) has no rule yet, so it is missed in every seed.")


if __name__ == "__main__":
    main()
