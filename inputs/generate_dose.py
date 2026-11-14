"""
Personal dose generator (R21): one dosimeter reading per astronaut per mission day, plus the dose each
astronaut had before this mission, so the career-limit rule (600 mSv, V039) has an input.

There is no real per-astronaut dose data in our sources (dosimetry is only an image, RA p53, V059), so this is
SIMULATED, built on real ISS area dose:
  - base = DosTel1 absorbed dose for that mission day's replay date, as the server computed it
    (env_daily, source 'RadLab DosTel1', complete days only)
  - Gy -> Sv: median of ALTEA dose_eq_uSv_day / absorbed_dose_uGy_day on the same complete days.
    DERIVED from our data; it is ALTEA's ratio (2010–2012) applied to DosTel1 (2024): a stretch, stated as such.
  - personal factor per astronaut ~ N(1, 0.05): TEAM DESIGN (position and shielding differ between people)
  - days with no complete DosTel1 value (e.g. mission days 1–23) use the median complete day: TEAM DESIGN
  - EVA extra dose: LEFT OUT (no source)
  - dose before this mission: TEAM DESIGN; A4 is set high so the career rule can fire (scenario R1)

Run after send_radlab.py (needs env_daily in data/health.db). Writes data/generated/dose_readings.csv and
data/generated/dose_anomaly_labels.csv; then run send_virtual.py and load_db.py again.
Usage: python inputs/generate_dose.py
"""
import os
import sqlite3

import numpy as np
import pandas as pd

OUT = os.environ.get("SIM_OUT", "data/generated")
DB = "data/health.db"
SEED = 11
CAREER_LIMIT_MSV = 600                         # V039
PERSONAL_SD = 0.05                             # TEAM DESIGN
PRIOR_CAREER_MSV = {"A1": 120, "A2": 60, "A3": 30, "A4": 470}   # TEAM DESIGN; A4 = scenario R1


def main():
    rng = np.random.default_rng(SEED + int(os.environ.get("SIM_SEED_OFFSET", 0)))   # offset: validate_seeds.py
    tl = pd.read_csv(f"{OUT}/mission_timeline.csv")
    with sqlite3.connect(DB) as con:
        d = pd.read_sql("SELECT date, metric, source, value FROM env_daily WHERE complete = 1 AND source IN "
                        "('RadLab DosTel1', 'RadLab ALTEA-Survey')", con)
    dos = d[(d.source == "RadLab DosTel1") & (d.metric == "absorbed_dose_uGy_day")].set_index("date")["value"]
    alt = d[d.source == "RadLab ALTEA-Survey"].pivot(index="date", columns="metric", values="value").dropna()
    if dos.empty or alt.empty:
        raise SystemExit("No complete RadLab days in env_daily: run send_radlab.py first.")
    q = float((alt["dose_eq_uSv_day"] / alt["absorbed_dose_uGy_day"]).median())     # DERIVED
    fallback = float(dos.median())

    rows, missing = [], 0
    factor = {a: rng.normal(1, PERSONAL_SD) for a in PRIOR_CAREER_MSV}
    for r in tl.itertuples():
        base = dos.get(r.replay_date)
        if base is None:
            base, missing = fallback, missing + 1
        for a in PRIOR_CAREER_MSV:
            msv = base * q * factor[a] / 1000                                       # uGy -> uSv -> mSv
            rows.append({"astronaut_id": a, "date": r.date, "mission_day": r.mission_day, "indicator_id": "R21",
                         "metric": "personal_dose_mSv", "value": round(msv, 4), "unit": "mSv",
                         "source": "dose-simulator", "is_real": 0})
    for a, prior in PRIOR_CAREER_MSV.items():
        rows.append({"astronaut_id": a, "date": tl.date.iloc[0], "mission_day": 1, "indicator_id": "R21",
                     "metric": "career_dose_before_mission_mSv", "value": prior, "unit": "mSv",
                     "source": "dose-simulator", "is_real": 0})
    df = pd.DataFrame(rows)

    # label: first day the projected career dose passes 600 mSv
    # projection = before mission + received so far + mean daily so far x days left (TEAM DESIGN, same as features.py)
    days, labels = len(tl), []
    for a, prior in PRIOR_CAREER_MSV.items():
        s = df[(df.astronaut_id == a) & (df.metric == "personal_dose_mSv")].sort_values("mission_day")
        cum = s.value.cumsum().values
        proj = prior + cum + cum / np.arange(1, days + 1) * (days - np.arange(1, days + 1))
        actual = prior + cum
        over = np.nonzero(proj > CAREER_LIMIT_MSV)[0]
        hit = np.nonzero(actual > CAREER_LIMIT_MSV)[0]
        red_from = int(hit[0]) + 1 if len(hit) else None
        if len(over):
            labels.append([a, "R21", "R1_career_dose_on_track_over_600", int(over[0]) + 1,
                           (red_from - 1) if red_from else days, "orange", 0])
        if red_from:
            labels.append([a, "R21", "R1_career_dose_over_600", red_from, days, "red", 0])
        print(f"{a}: mission {cum[-1]:.0f} mSv, career at landing {actual[-1]:.0f} mSv"
              + (f", orange from day {over[0] + 1}" if len(over) else "")
              + (f", red from day {red_from}" if red_from else ""))

    os.makedirs(OUT, exist_ok=True)
    df.to_csv(f"{OUT}/dose_readings.csv", index=False)
    pd.DataFrame(labels, columns=["astronaut_id", "indicator_id", "scenario", "start_day", "end_day",
                                  "expected_level", "is_decoy"]).to_csv(f"{OUT}/dose_anomaly_labels.csv", index=False)
    print(f"Gy->Sv ratio from ALTEA (derived): {q:.2f} | DosTel1 base: {len(tl) - missing} real days, "
          f"{missing} days filled with the median ({fallback:.0f} uGy/day)")


if __name__ == "__main__":
    main()
