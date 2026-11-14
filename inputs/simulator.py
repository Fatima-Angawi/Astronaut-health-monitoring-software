"""
Mission simulator – core crew data for 4 astronauts × 180 days.

Writes to OUT (same folder generate_behavior.py and the bone generator use):
  crew.csv              A1–A4 profiles (personal means; preflight BMD is in bone_preflight.csv from generate_bone.py)
  mission_timeline.csv  mission_day, date, replay_date (real date for DONKI/RadLab/EDA), gravity, phase
  mission_events.csv    EVAs, dockings, landing (critical = 1 → R01/R01c red rule)
  sim_readings.csv      long format: sleep, PVT, KSS, work hours, HR/BP, symptoms, medical events, CO2, SpO2
  anomaly_labels.csv    adds rows for R01, R01c, R01d, R01f, R10b, R06, R03c (keeps R02*/R18 rows)

Every number is either from the knowledge base (Value ID in a comment) or a TEAM DESIGN value.
Optional overrides: sim_params.json next to this script's working directory.

Usage:  python inputs/simulator.py
"""
import json, os
import numpy as np
import pandas as pd

OUT = os.environ.get("SIM_OUT", "data/generated")      # one folder for all generated data
os.makedirs(OUT, exist_ok=True)

P = {
    "_label": "Team design unless a Value ID is given",
    "seed": 7,
    "crew": ["A1", "A2", "A3", "A4"],
    "cmo": "A1",                                   # crew medical officer (one per crew, V048)
    "days": 180,
    "start_date": "2026-11-15",                    # simulated calendar
    "replay_start": "2024-01-01",                  # real date replayed on mission day 1 (DosTel1 covers 2024-01..10)
    # sleep (R01): flight study means ~6.0–6.5 h (V002); individual need varies (V006); SD not sourced (V004)
    "sleep_mean": {"mean": 6.4, "sd_between": 0.15}, "sleep_sd_daily": 0.5,
    # work hours (R01f): nominal 6.5 h/day (V022) → normal days just under it
    "work_weekday": {"mean": 6.2, "sd": 0.5}, "work_weekend": {"mean": 3.0, "sd": 1.0},
    # PVT-B 3-min (R01c): team design response to sleep debt
    "pvt": {"debt_free_h": 0.5,            # sleep debt below this has no effect (team design)
            "lapses_base": 2.0, "lapses_per_excess_h": 4.0,
            "slowest10_base_ms": 420, "slowest10_per_excess_ms": 120, "slowest10_noise_ms": 30,
            "mean_rt_base_ms": 270, "mean_rt_per_excess_ms": 40, "mean_rt_noise_ms": 15},
    # KSS (R01d): scale 1–9 to verify (V020); sleepiness rises only modestly (V019)
    "kss": {"base": 4.0, "per_debt_h": 0.5},
    # HR/BP (R10b): in-flight values lower than preflight (V030); normal values not sourced (V032)
    "hr": {"mean": 58, "sd_between": 4, "sd_daily": 2.0},
    "bp": {"sys": 112, "dia": 70, "sd_between": 6, "sd_daily_sys": 4, "sd_daily_dia": 3},
    # symptoms (R06): 26.21 events per person-year on ISS (V034), mix from Table 2 counts (V035)
    "symptom_rate_per_year": 26.21,
    "symptom_weights": {"nasal_congestion": 389, "back_pain": 382, "space_motion_sickness": 325,
                        "insomnia": 299, "headache": 233},
    # CO2 (R03c): ISS ~2500 ppm (V044); headache link above 2.5 mmHg ≈ 3290 ppm (V045, V046)
    # daily value = highest rolling 1-hour average, matching NASA-STD-3001 Vol 2 [V2 6004] (1-hour limit 3 mmHg, V066)
    "co2": {"mean": 2500, "sd": 150, "high": 3600, "over_limit": 4100},
    # SpO2 (R06b): no sourced values (V038) → placeholder
    "spo2": {"mean": 97.0, "sd": 0.8},
}
if os.path.exists("sim_params.json"):
    P.update(json.load(open("sim_params.json")))
rng = np.random.default_rng(P["seed"])
CREW, DAYS = P["crew"], P["days"]
days = np.arange(1, DAYS + 1)
start, replay = pd.Timestamp(P["start_date"]), pd.Timestamp(P["replay_start"])

# ------------------------------------------------------------------ 1. crew
crew = []
for a in CREW:
    crew.append({
        "astronaut_id": a, "role": "CMO" if a == P["cmo"] else "crew",
        "sleep_mean_h": round(rng.normal(P["sleep_mean"]["mean"], P["sleep_mean"]["sd_between"]), 2),
        "hr_mean_bpm": round(rng.normal(P["hr"]["mean"], P["hr"]["sd_between"]), 1),
        "bp_sys_mean": round(rng.normal(P["bp"]["sys"], P["bp"]["sd_between"]), 1),
        "bp_dia_mean": round(rng.normal(P["bp"]["dia"], P["bp"]["sd_between"] * 0.7), 1),
    })                                             # preflight aBMD comes from generate_bone.py (bone_preflight.csv)
crew_df = pd.DataFrame(crew).set_index("astronaut_id")
crew_df.reset_index().to_csv(f"{OUT}/crew.csv", index=False)

# ------------------------------------------------------------------ 2. timeline
timeline = pd.DataFrame({
    "mission_day": days,
    "date": [(start + pd.Timedelta(days=int(d) - 1)).strftime("%Y-%m-%d") for d in days],
    "replay_date": [(replay + pd.Timedelta(days=int(d) - 1)).strftime("%Y-%m-%d") for d in days],
    "gravity_level": 0.0,                          # ISS microgravity throughout
    "phase": "orbit",
})
timeline.to_csv(f"{OUT}/mission_timeline.csv", index=False)
def date_of(d):
    return (start + pd.Timedelta(days=int(d) - 1)).strftime("%Y-%m-%d")

# ------------------------------------------------------------------ 3. events
# replay_start 2024-01-01 → the 12 Feb 2024 SPE (DONKI) falls on mission day 43
events = [
    {"mission_day": 30,  "astronaut_id": None, "type": "docking",   "critical": 1},
    {"mission_day": 43,  "astronaut_id": "A3", "type": "EVA",       "critical": 1},   # same day as 2024-02-12 SPE (R21b demo)
    {"mission_day": 67,  "astronaut_id": "A2", "type": "EVA",       "critical": 1},   # day after A2's short-sleep week → R01/R01c red
    {"mission_day": 110, "astronaut_id": None, "type": "docking",   "critical": 1},
    {"mission_day": 140, "astronaut_id": "A4", "type": "EVA",       "critical": 1},
    {"mission_day": 150, "astronaut_id": None, "type": "undocking", "critical": 1},
    {"mission_day": 180, "astronaut_id": None, "type": "landing",   "critical": 1},
]
ev = pd.DataFrame(events)
ev["start_time"] = [f"{date_of(d)}T08:00Z" for d in ev.mission_day]
ev["end_time"] = [f"{date_of(d)}T15:00Z" for d in ev.mission_day]
ev.to_csv(f"{OUT}/mission_events.csv", index=False)
docking_weeks = [range(27, 31), range(107, 111)]   # four 10-h days before each docking → critical overload (V024)

# ------------------------------------------------------------------ 4. readings
rows, labels = [], []
def add(a, d, ind, metric, value, unit):
    rows.append({"astronaut_id": a, "date": date_of(d), "mission_day": int(d), "indicator_id": ind,
                 "metric": metric, "value": value, "unit": unit, "source": "simulator", "is_real": 0})
def label(a, ind, scenario, s, e, level, decoy=0):
    labels.append({"astronaut_id": a, "indicator_id": ind, "scenario": scenario, "start_day": s,
                   "end_day": e, "expected_level": level, "is_decoy": decoy})

# cabin CO2: one value per day for the whole crew (cabin-level)
co2 = {d: rng.normal(P["co2"]["mean"], P["co2"]["sd"]) for d in days}
for d in range(80, 85):
    co2[d] = rng.normal(P["co2"]["high"], 80)                       # SD 80 = team design; scenario: high CO2 days 80–84 (above 2.5 mmHg)
co2[82] = P["co2"]["over_limit"]                                 # one day above 3 mmHg (≈3,950 ppm) → orange test

sym_types = list(P["symptom_weights"])
sym_p = np.array(list(P["symptom_weights"].values()), float); sym_p /= sym_p.sum()
p_symptom_day = P["symptom_rate_per_year"] / 365                  # ≈ 0.072 per person-day (V034)

for a in CREW:
    c = crew_df.loc[a]
    sleep_hist = []
    for d in days:
        weekend = d % 7 in (6, 0)
        busy = any(d in w for w in docking_weeks)

        # --- work hours (R01f)
        if busy:
            work = rng.normal(10.3, 0.15)                            # team design values;≥ 10 h → counts as a 10-h day (V024)
        elif a == "A2" and 58 <= d <= 66:
            work = rng.normal(9.5, 0.3)                              # team design: explains A2's short sleep
        else:
            w = P["work_weekend"] if weekend else P["work_weekday"]
            work = rng.normal(w["mean"], w["sd"])
        work = float(np.clip(work, 0, 14))                               # team design: plausible range

        # --- sleep (R01)
        sleep = rng.normal(c.sleep_mean_h, P["sleep_sd_daily"])
        if busy:                                 sleep -= 0.5                # team design
        if a == "A2" and 60 <= d <= 66:          sleep = rng.normal(4.8, 0.3)  # team design: short-sleep week
        if a == "A2" and 120 <= d <= 135:        sleep = rng.normal(5.2, 0.3)  # team design: underreporting scenario
        if a == "A1" and d == 100:               sleep = 4.5                 # team design; decoy: one bad night
        sleep = float(np.clip(sleep, 2.5, 10))                               # team design: plausible range
        sleep_hist.append(sleep)
        debt = max(0.0, c.sleep_mean_h - float(np.mean(sleep_hist[-3:])))    # 3-night debt window = team design

        # --- PVT + KSS (R01c, R01d), one session per day at a fixed time after waking
        pv = P["pvt"]
        excess = max(0.0, debt - pv["debt_free_h"])
        lam = pv["lapses_base"] + pv["lapses_per_excess_h"] * excess
        if a == "A2" and 120 <= d <= 135:        lam += 3                    # supports underreporting scenario (team design)
        lapses = int(rng.poisson(lam))
        slow10 = pv["slowest10_base_ms"] + pv["slowest10_per_excess_ms"] * excess + rng.normal(0, pv["slowest10_noise_ms"])
        if a == "A2" and 120 <= d <= 135:        slow10 += 60                # supports underreporting scenario (team design)
        mean_rt = pv["mean_rt_base_ms"] + pv["mean_rt_per_excess_ms"] * excess + rng.normal(0, pv["mean_rt_noise_ms"])
        kss = P["kss"]["base"] + min(P["kss"]["per_debt_h"] * debt, 1.5) + rng.normal(0, 0.6)   # plateaus (V019); cap 1.5 and noise 0.6 = team design
        if a == "A2" and 120 <= d <= 135:        kss = rng.normal(3.5, 0.4)  # team design: feels alert while PVT worsens → R01d
        kss = int(np.clip(round(kss), 1, 9))

        # --- HR / BP (R10b), daily resting value after waking
        hr = rng.normal(c.hr_mean_bpm, P["hr"]["sd_daily"])
        if a == "A2" and 70 <= d <= 73:          hr += 12                     # team design: 3-day HR rise scenario
        if a == "A3" and d == 50:                hr += 9                      # team design; decoy: one high day
        sys_bp = rng.normal(c.bp_sys_mean, P["bp"]["sd_daily_sys"])
        dia_bp = rng.normal(c.bp_dia_mean, P["bp"]["sd_daily_dia"])

        # --- symptoms + medical events (R06)
        symptom = None
        if a == "A4" and 80 <= d <= 84:
            symptom = "headache"                                             # CO2 scenario
        elif rng.random() < p_symptom_day:
            symptom = rng.choice(sym_types, p=sym_p)
            if symptom == "space_motion_sickness" and d > 5:                 # space adaptation, early days only
                symptom = "nasal_congestion"
        medical = 1 if (a == "A2" and d == 95) else 0                        # e.g. head bump → extra cognitive test

        # --- SpO2 (R06b), placeholder
        spo2 = float(np.clip(rng.normal(P["spo2"]["mean"], P["spo2"]["sd"]), 90, 100))

        add(a, d, "R01",  "sleep_h", round(sleep, 2), "h")
        add(a, d, "R01f", "work_hours", round(work, 2), "h")
        add(a, d, "R01c", "pvt_lapses", lapses, "count")
        add(a, d, "R01c", "pvt_slowest10_ms", round(slow10, 1), "ms")
        add(a, d, "R01c", "pvt_mean_rt_ms", round(mean_rt, 1), "ms")
        add(a, d, "R01d", "kss", kss, "score_1_9")
        add(a, d, "R10b", "hr_resting", round(hr, 1), "bpm")
        add(a, d, "R10b", "bp_systolic", round(sys_bp), "mmHg")
        add(a, d, "R10b", "bp_diastolic", round(dia_bp), "mmHg")
        add(a, d, "R06",  "symptom_logged", int(symptom is not None), "bool")
        if symptom:
            add(a, d, "R06", f"symptom_{symptom}", 1, "bool")
        add(a, d, "R06",  "headache", int(symptom == "headache"), "bool")
        add(a, d, "R06",  "medical_event", medical, "bool")
        add(a, d, "R06b", "spo2", round(spo2, 1), "%")
        add(a, d, "R03c", "co2_1h_max_ppm", round(co2[d]), "ppm")

# ------------------------------------------------------------------ 5. labels (ground truth, tests only)
label("A2", "R01",  "S1_short_sleep_week", 62, 66, "orange")      # 7-day mean < 6 h from ~day 62; with PVT yellow → orange
label("A2", "R01",  "S2_tired_before_eva", 66, 66, "red")         # orange within 24 h of the day-67 EVA
label("A2", "R01c", "S3_pvt_after_short_sleep", 61, 68, "orange")
label("A2", "R01d", "S4_feels_alert_pvt_bad", 120, 135, "yellow")
label("A2", "R01f", "S5_long_days_before_short_sleep", 58, 66, "red")
for w in docking_weeks:
    for a in CREW:
        label(a, "R01f", "S6_docking_week_overload", w.start, w.stop - 1, "red")
label("A2", "R10b", "S7_hr_rise_3_days", 70, 73, "orange")
label("A4", "R06",  "S8_headache_5_days", 80, 84, "orange")
for w in docking_weeks:
    for a in CREW:
        label(a, "R01", "S11_docking_week_sleep", w.start + 3, w.stop + 2, "yellow")   # busy week, 0.5 h less sleep
label("A4", "R03c", "S9_high_co2_with_headache", 80, 84, "yellow")
for a in CREW:
    label(a, "R03c", "S12_co2_over_3mmHg_1h", 82, 82, "orange")    # cabin-wide, [V2 6004]
label("A2", "R06",  "S10_medical_event", 95, 95, "yellow")
label("A1", "R01",  "D_one_bad_night", 100, 100, "none", 1)
label("A3", "R10b", "D_one_high_hr_day", 50, 50, "none", 1)

# ------------------------------------------------------------------ 6. write
pd.DataFrame(rows).to_csv(f"{OUT}/sim_readings.csv", index=False)
lab_path = f"{OUT}/anomaly_labels.csv"
mine = {"R01", "R01c", "R01d", "R01f", "R10b", "R06", "R03c"}
new = pd.DataFrame(labels)
if os.path.exists(lab_path):
    old = pd.read_csv(lab_path)
    new = pd.concat([old[~old.indicator_id.isin(mine)], new], ignore_index=True)
new.to_csv(lab_path, index=False)

r = pd.DataFrame(rows)
print(f"{OUT}/crew.csv, mission_timeline.csv ({DAYS} days), mission_events.csv ({len(ev)} events)")
print(f"sim_readings.csv: {len(r):,} rows, {r.metric.nunique()} metrics")
print(f"anomaly_labels.csv: {len(labels)} simulator rows added")
print("Mission day 43 =", timeline.loc[42, "replay_date"], "(replayed real date; DONKI SPE 2024-02-12)")
