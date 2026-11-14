"""
R18 bone generator: what a real flight could record for bone, plus the answer key for testing.

Bone density is NOT measured in flight: DXA is done within 45 days before launch and ~5 days after landing
(Fracture ER p15). So this script sends only the in-flight INPUTS (exercise, ARED load, vitamin D, falls,
body weight) and the post-flight DXA (availability = after_return). The projected % of preflight is computed
by the engine (engine/features.py); bone_truth.csv holds the expected projection so the tests can check it.

Run after inputs/simulator.py (it reads the shared timeline and events) and BEFORE generate_behavior.py
(which reads exercise_minutes from here as a driver: one exercise drop affects both mood and bone).

Outputs (data/generated/):
  bone_readings.csv        astronaut_id, date, mission_day, indicator_id, metric, value, unit, source, is_real, availability
  bone_preflight.csv       astronaut_id, dxa_date, preflight_abmd_total_hip, _lumbar_spine, _femoral_neck
  bone_truth.csv           astronaut_id, mission_day, site, projected_bmd_pct, adherent   (never sent to the API)
  bone_anomaly_labels.csv  same columns as anomaly_labels.csv

Evidence (Fracture ER = NASA Evidence Report, Risk of Bone Fracture; Rev C = NASA-STD-3001 Vol 1 Rev C):
  - Monthly BMD change, Table 4 p22: with ARED trochanter -0.5 %, spine -0.32 %; before ARED -1.56 %, -1.06 %.
  - ARED loads 2-3x body weight (p22).
  - DXA timing (p15). Limits: hip/spine >= 95 %, femoral neck >= 90 % of preflight, Rev C [V1 4027] p39.
  - A fall during EVA is a fracture-risk event (Fracture ER, fracture-risk event definition).
Team design / assumptions (marked on each line):
  - Exercise minutes 90 +/- 20 per day: placeholder carried over from generate_behavior.py (no prescription in
    our sources: Rev C [V1 4014] gives no number). ASSUMPTION.
  - Adherence = 7-day mean exercise >= 75 % of the astronaut's own median; adherent days use the ARED rate,
    non-adherent days the pre-ARED rate. TEAM DESIGN.
  - Hip and femoral neck use the trochanter rate (Table 4 has no separate rate). ASSUMPTION.
  - Preflight aBMD, DXA dates and body weights: the teammate's synthetic values (bone_params.json).
"""
import os
import numpy as np
import pandas as pd

OUT = os.environ.get("SIM_OUT", "data/generated")
SEED = 7
DAYS_PER_MONTH = 30.44
RATES = {                                     # %/month, Fracture ER Table 4 p22
    "ared":     {"total_hip": -0.5,  "femoral_neck": -0.5,  "lumbar_spine": -0.32},
    "pre_ared": {"total_hip": -1.56, "femoral_neck": -1.56, "lumbar_spine": -1.06},
}
LIMITS = {"total_hip": 95, "lumbar_spine": 95, "femoral_neck": 90}     # Rev C [V1 4027] p39
PREFLIGHT = {   # g/cm2 and DXA date: teammate's synthetic values (bone_params.json), all <= 45 days before launch
    "A1": ("2026-11-02", 1.032, 1.004, 0.912),
    "A2": ("2026-11-07", 1.093, 1.116, 0.982),
    "A3": ("2026-10-25", 0.935, 0.980, 0.851),
    "A4": ("2026-10-08", 0.933, 0.930, 0.824),
}
BODY_WEIGHT = {"A1": 85.7, "A2": 78.4, "A3": 82.1, "A4": 71.2}         # kg, teammate's synthetic values
EX_MEAN, EX_SD = 90, 20                       # min/day, ASSUMPTION (placeholder, see docstring)
ADHERENCE = 0.75                              # TEAM DESIGN
BASELINE_DAYS = (1, 14)                       # TEAM DESIGN: same baseline window as engine/features.py
ARED_LOAD = (2.0, 3.0)                        # x body weight on a full session, Fracture ER p22
DXA_NOISE_PCT = 0.5                           # TEAM DESIGN: post-flight DXA measurement noise (1 SD, %)
POSTFLIGHT_DAY_AFTER_LANDING = 5              # Fracture ER p15

# Scenarios (TEAM DESIGN)
A2_LOW_EXERCISE = [(60, 80), (125, 170)]      # A2 exercise drop: busy weeks, then a long decline
LOW_EX_MEAN, LOW_EX_SD = 30, 10
DECOY = ("A3", 90)                            # one missed session: must NOT alert
FALL = ("A2", 67)                             # fall during A2's EVA (mission_events.csv)
VIT_D_GAP = ("A4", 140, 154)                  # same days as behavior scenario 6 (countermeasure gap)


def main():
    rng = np.random.default_rng(SEED)
    tl = pd.read_csv(f"{OUT}/mission_timeline.csv")
    ev = pd.read_csv(f"{OUT}/mission_events.csv")
    date_of = dict(zip(tl.mission_day, tl.date))
    days = list(tl.mission_day)
    landing = int(ev.loc[ev.type == "landing", "mission_day"].iloc[0]) if (ev.type == "landing").any() else days[-1]
    eva_days = {(r.astronaut_id, int(r.mission_day)) for r in ev.itertuples() if r.type == "EVA"}
    if (FALL[0], FALL[1]) not in eva_days:
        print(f"note: fall day {FALL} is not an EVA day in mission_events.csv")

    rows, truth, labels = [], [], []
    def add(a, d, metric, value, unit, date=None, availability="live"):
        rows.append({"astronaut_id": a, "date": date or date_of[d], "mission_day": d, "indicator_id": "R18",
                     "metric": metric, "value": value, "unit": unit, "source": "bone-simulator",
                     "is_real": 0, "availability": availability})

    for a in PREFLIGHT:
        # exercise per day
        ex = {}
        for d in days:
            low = a == "A2" and any(s <= d <= e for s, e in A2_LOW_EXERCISE)
            m, sd = (LOW_EX_MEAN, LOW_EX_SD) if low else (EX_MEAN, EX_SD)
            ex[d] = max(0, round(rng.normal(m, sd)))
        if a == DECOY[0]:
            ex[DECOY[1]] = 0
        median = float(np.median([ex[d] for d in days if BASELINE_DAYS[0] <= d <= BASELINE_DAYS[1]]))   # same baseline as engine/features.py
        pct = {s: 100.0 for s in LIMITS}
        for d in days:
            week = [ex[x] for x in range(max(days[0], d - 6), d + 1)]
            adherent = int(np.mean(week) >= ADHERENCE * median)
            for s in pct:
                pct[s] += RATES["ared" if adherent else "pre_ared"][s] / DAYS_PER_MONTH
                truth.append({"astronaut_id": a, "mission_day": d, "site": s,
                              "projected_bmd_pct": round(pct[s], 3), "adherent": adherent})
            load = round(float(np.clip(rng.uniform(*ARED_LOAD) * min(1, ex[d] / EX_MEAN), 0, 3)), 2)
            vit_d = 0 if (a == VIT_D_GAP[0] and VIT_D_GAP[1] <= d <= VIT_D_GAP[2]) else 1
            add(a, d, "exercise_minutes", ex[d], "min")
            add(a, d, "exercise_load_x_bw", load, "x_bw")
            add(a, d, "vitamin_d_taken", vit_d, "bool")
            add(a, d, "fall_or_impact_event", int((a, d) == FALL), "bool")
            if (d - days[0]) % 7 == 0:
                add(a, d, "body_weight", round(BODY_WEIGHT[a] + rng.normal(0, 0.3), 1), "kg")

        # post-flight DXA = preflight x projection at landing, with measurement noise
        dxa_date, *pre = PREFLIGHT[a]
        post_day = landing + POSTFLIGHT_DAY_AFTER_LANDING
        post_date = (pd.Timestamp(date_of[landing]) + pd.Timedelta(days=POSTFLIGHT_DAY_AFTER_LANDING)).strftime("%Y-%m-%d")
        end = {t["site"]: t["projected_bmd_pct"] for t in truth if t["astronaut_id"] == a and t["mission_day"] == landing}
        for s, p in zip(["total_hip", "lumbar_spine", "femoral_neck"], pre):
            v = p * end[s] / 100 * (1 + rng.normal(0, DXA_NOISE_PCT) / 100)
            add(a, post_day, f"postflight_abmd_{s}", round(v, 4), "g/cm2", date=post_date, availability="after_return")

    # labels from the answer key
    tr = pd.DataFrame(truth)
    def first(a, s, below):
        x = tr[(tr.astronaut_id == a) & (tr.site == s) & (tr.projected_bmd_pct < below)]
        return int(x.mission_day.min()) if len(x) else None
    for a in PREFLIGHT:
        y = first(a, "total_hip", 97)
        o = [d for d in (first(a, s, LIMITS[s]) for s in LIMITS) if d]
        if y:
            labels.append([a, "R18", "B1_exercise_drop_bmd_projection", y, landing, "yellow", 0])
        if o:
            labels.append([a, "R18", "B1_exercise_drop_bmd_projection", min(o), landing, "orange", 0])
    labels.append([DECOY[0], "R18", "D_one_missed_exercise", DECOY[1], DECOY[1], "none", 1])
    labels.append([FALL[0], "R18", "B2_fall_during_eva", FALL[1], FALL[1], "context", 0])
    labels.append([VIT_D_GAP[0], "R18", "B3_vitamin_d_gap", VIT_D_GAP[1], VIT_D_GAP[2], "context", 0])

    os.makedirs(OUT, exist_ok=True)
    pd.DataFrame(rows).to_csv(f"{OUT}/bone_readings.csv", index=False)
    pd.DataFrame([{"astronaut_id": a, "dxa_date": v[0], "preflight_abmd_total_hip": v[1],
                   "preflight_abmd_lumbar_spine": v[2], "preflight_abmd_femoral_neck": v[3]}
                  for a, v in PREFLIGHT.items()]).to_csv(f"{OUT}/bone_preflight.csv", index=False)
    tr.to_csv(f"{OUT}/bone_truth.csv", index=False)
    pd.DataFrame(labels, columns=["astronaut_id", "indicator_id", "scenario", "start_day", "end_day",
                                  "expected_level", "is_decoy"]).to_csv(f"{OUT}/bone_anomaly_labels.csv", index=False)

    # check
    print(f"bone_readings.csv: {len(rows):,} rows")
    endtab = tr[tr.mission_day == landing].pivot(index="astronaut_id", columns="site", values="projected_bmd_pct")
    print("projected % of preflight at landing:\n", endtab.round(2).to_string())
    for a in PREFLIGHT:
        print(a, {f"{s}<{lim}": first(a, s, lim) for s, lim in
                  [("total_hip", 97), ("total_hip", 95), ("lumbar_spine", 95), ("femoral_neck", 90)]})


if __name__ == "__main__":
    main()
