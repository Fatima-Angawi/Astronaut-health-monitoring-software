"""
Behavioral indicator generator (R02e mood/stress, R02 WinSCAT-like cognition, R02c PPC, R02d PMC)
Spec: "Behavioral Data Spec" artifact. All coefficients are TEAM DESIGN values (NASA has no
validated behavioral thresholds, V026).

Reads (if present) from data/generated/:
  mission_timeline.csv          mission_day, date, ...
  readings.csv / *_readings.csv  metrics: sleep_h (R01), work_hours (R01f), co2_1h_max_ppm (R03c),
                                 headache (R06), medical_event (R06)
Missing drivers are replaced by clearly labelled STUB values so the script runs on its own.

Writes to data/generated/:
  behavior_readings.csv   long format (shared contract)
  behavior_truth.csv      true_mood / true_stress / true_cognition (tests only)
  anomaly_labels.csv      appends R02* rows (replaces previous R02* rows)

Usage:  python inputs/generate_behavior.py           (uses behavior_params.json if present)
"""
import glob, json, os
import numpy as np
import pandas as pd

OUT = "data/generated"
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ parameters
DEFAULT = {
    "_label": "Team design values – NASA has no validated behavioral thresholds (V026)",
    "seed": 42, "crew": ["A1", "A2", "A3", "A4"], "days": 180, "start_date": "2026-11-15",
    "mood_baseline": {"mean": 3.9, "sd_between_people": 0.3},
    "stress_baseline": {"mean": 2.1, "sd_between_people": 0.3},
    "noise": {"sd_mood": 0.35, "sd_stress": 0.35, "sd_cog": 0.4},
    "mood": {"a": 0.35, "b": 0.10, "c": 0.50, "d": 0.30, "e": 0.15},
    "stress": {"a_s": 0.30, "b_s": 0.15, "c_s": 0.40, "d_s": 0.30, "e_s": 0.15},
    "cognition": {"f": 0.25, "g": 1.0, "medical_effect_days": 3, "ceiling_z": 0.8,
                  "preflight_sessions": 3, "monthly_days": [30, 60, 90, 120, 150, 180],
                  "ability_offset": {"A3": 2.0}},   # A3 = high performer above the ceiling (scenario 8)
    "countermeasures": {"family_contact_prob": 0.4,
                        "leisure_minutes": {"mean": 45, "sd": 15},
                        "exercise_minutes": {"mean": 90, "sd": 20}},   # placeholder until sourced
    "sessions": {"ppc_every_days": 14, "pmc_every_days": 7,
                 "concern_raised_prob_normal": 0.05, "concern_raised_prob_when_low_mood": 0.6},
    "co2_headache_ppm": 3290,   # 2.5 mmHg ≈ 3,290 ppm at 760 mmHg (V045, V046)
    "work_nominal_h": 6.5,      # NASA nominal daily limit (V022)
}
P = json.load(open("behavior_params.json")) if os.path.exists("behavior_params.json") else DEFAULT
for k, v in DEFAULT.items():
    P.setdefault(k, v)
rng = np.random.default_rng(P["seed"] + int(os.environ.get("SIM_SEED_OFFSET", 0)))   # offset: validate_seeds.py
CREW, DAYS = P["crew"], P["days"]
days = np.arange(1, DAYS + 1)

# ------------------------------------------------------------------ timeline
tl_path = f"{OUT}/mission_timeline.csv"
if os.path.exists(tl_path):
    tl = pd.read_csv(tl_path)
    date_of = dict(zip(tl.mission_day, pd.to_datetime(tl.date)))
    start = date_of.get(1, pd.Timestamp(P["start_date"]))
else:
    start = pd.Timestamp(P["start_date"])
    date_of = {}
def to_date(d):
    return date_of.get(d, start + pd.Timedelta(days=int(d) - 1))

# ------------------------------------------------------------------ drivers
def load_driver(metric):
    """Return {(astronaut, day): value} from any generated readings file, or None."""
    files = [f for f in glob.glob(f"{OUT}/*readings*.csv") if "behavior_readings" not in f]
    rows = []
    for f in files:
        df = pd.read_csv(f)
        if {"metric", "astronaut_id", "mission_day", "value"} <= set(df.columns):
            rows.append(df[df.metric == metric])
    if not rows or sum(len(r) for r in rows) == 0:
        return None
    df = pd.concat(rows).groupby(["astronaut_id", "mission_day"])["value"].mean()
    return df.to_dict()

stubs_used = []
def driver(metric, stub_fn):
    d = load_driver(metric)
    if d is None:
        stubs_used.append(metric)
        d = {(a, t): stub_fn(a, t) for a in CREW for t in days}
    return d

# STUBS (only used when the other modules have not been generated yet)
stub_sleep_mean = {a: rng.normal(6.2, 0.3) for a in CREW}
def stub_sleep(a, t):
    v = rng.normal(stub_sleep_mean[a], 0.5)
    if a == "A2" and 60 <= t <= 66:  v = rng.normal(4.8, 0.3)    # A2 short-sleep week (sleep module)
    if a == "A2" and 120 <= t <= 135: v = rng.normal(5.2, 0.3)   # supports scenario 3
    return round(max(v, 0), 2)
def stub_work(a, t):
    return round(max(rng.normal(6.3, 0.6), 0), 2)
def stub_co2(a, t):
    if a == "A4" and 80 <= t <= 84:
        return round(rng.normal(3600, 100))                        # scenario 4
    return round(rng.normal(2500, 200))
def stub_headache(a, t):
    return 1 if (a == "A4" and 80 <= t <= 84) else 0
def stub_medical(a, t):
    return 1 if (a == "A2" and t == 95) else 0                     # scenario 7
def stub_exercise(a, t):
    ex = P["countermeasures"]["exercise_minutes"]                  # = CM, which is only defined further down
    return max(0, round(rng.normal(ex["mean"], ex["sd"])))

sleep = driver("sleep_h", stub_sleep)
work = driver("work_hours", stub_work)
co2 = driver("co2_1h_max_ppm", stub_co2)
headache = driver("headache", stub_headache)
medical = driver("medical_event", stub_medical)
exercise_d = driver("exercise_minutes", stub_exercise)             # produced by generate_bone.py (bone_readings.csv)

# ------------------------------------------------------------------ generation
M, S, C = P["mood"], P["stress"], P["cognition"]
CM, SES, N = P["countermeasures"], P["sessions"], P["noise"]
readings, truth, labels = [], [], []

def add(a, t, ind, metric, value, unit, source="simulator"):
    readings.append({"astronaut_id": a, "date": to_date(t).strftime("%Y-%m-%d"), "mission_day": int(t),
                     "indicator_id": ind, "metric": metric, "value": value, "unit": unit,
                     "source": source, "is_real": 0})

def label(a, ind, scenario, s, e, level, decoy=0):
    labels.append({"astronaut_id": a, "indicator_id": ind, "scenario": scenario,
                   "start_day": s, "end_day": e, "expected_level": level, "is_decoy": decoy})

scenario_windows = {"A2": [(60, 84), (93, 100), (118, 137)], "A3": [(38, 45), (100, 171)],
                    "A4": [(78, 86), (138, 162)], "A1": []}

for a in CREW:
    mood_base = rng.normal(P["mood_baseline"]["mean"], P["mood_baseline"]["sd_between_people"])
    stress_base = rng.normal(P["stress_baseline"]["mean"], P["stress_baseline"]["sd_between_people"])
    sleep_mean = np.mean([sleep[(a, t)] for t in days[:14]])
    ability = C.get("ability_offset", {}).get(a, 0.0)

    # decoy days: single bad days outside scenario windows
    # a 7-day rule stays true for up to 7 days after its cause ends, so decoys keep that distance from every
    # scenario and from the two docking weeks (27-30, 107-110), which affect the whole crew (TEAM DESIGN)
    busy = scenario_windows[a] + [(27, 33), (107, 113)]
    free = [t for t in days if t > 14 and not any(s <= t <= e + 7 for s, e in busy)]
    decoys = set(rng.choice(free, size=6, replace=False).tolist())
    for t in sorted(decoys):
        label(a, "R02e", "D_single_bad_day", t, t, "none", 1)

    # preflight cognition baseline (within 6 months before launch, BMed p59)
    pre_days = [-150, -90, -30][: C["preflight_sessions"]]
    pre_scores = [min(ability + rng.normal(0, N["sd_cog"]), C["ceiling_z"]) for _ in pre_days]
    pre_mean, pre_sd = np.mean(pre_scores), max(np.std(pre_scores, ddof=1), N["sd_cog"])
    for d, sc in zip(pre_days, pre_scores):
        add(a, d, "R02", "cognitive_score_z", round((sc - pre_mean) / pre_sd, 2), "z", "simulator:winscat_like")

    # extra cognitive sessions: day after a medical event, or after the first day of a high-CO2 run
    extra = set()
    for t in days:
        if medical[(a, t)] == 1 and t < DAYS:
            extra.add(t + 1)
        if co2[(a, t)] > P["co2_headache_ppm"] and (t == 1 or co2[(a, t - 1)] <= P["co2_headache_ppm"]) and t < DAYS:
            extra.add(t + 1)
    session_days = set(C["monthly_days"]) | extra

    recent_moods = []
    for t in days:
        # drivers
        prev = [sleep[(a, x)] for x in range(max(1, t - 3), t)] or [sleep[(a, t)]]
        sleep_debt = max(0.0, sleep_mean - float(np.mean(prev)))
        work_excess = max(0.0, work[(a, t)] - P["work_nominal_h"])
        co2_head = 1 if (co2[(a, t)] > P["co2_headache_ppm"] and headache[(a, t)] == 1) else 0

        # countermeasures
        fam = int(rng.random() < CM["family_contact_prob"])
        leisure = max(0, round(rng.normal(CM["leisure_minutes"]["mean"], CM["leisure_minutes"]["sd"])))
        exercise = exercise_d[(a, t)]
        if a == "A4" and 140 <= t <= 154:            # scenario 6: countermeasure gap
            fam = 0
        counter = fam + (leisure >= 30) + (exercise >= 60)

        # mood / stress (true)
        extra_mood, bias = 0.0, 0.0
        if a == "A2" and 67 <= t <= 75:   extra_mood -= 0.25 * (t - 66)            # scenario 1 ramp
        if a == "A2" and 76 <= t <= 82:   extra_mood -= 0.25 * 9 * (82 - t) / 7    # recovery
        if a == "A3" and 40 <= t <= 42:   extra_mood -= 2.0                        # scenario 2
        if a == "A2" and 120 <= t <= 135:                                         # scenario 3
            extra_mood -= 1.5 * min(1, (t - 119) / 5); bias = -extra_mood          # hides the decline
        if a == "A4" and t == 160:        extra_mood -= 2.5                        # scenario 5
        if t in decoys:                   extra_mood -= 1.5

        true_mood = (mood_base - M["a"] * sleep_debt - M["b"] * work_excess - M["c"] * co2_head
                     - M["d"] * t / DAYS + M["e"] * counter + extra_mood + rng.normal(0, N["sd_mood"]))
        true_stress = (stress_base + S["a_s"] * sleep_debt + S["b_s"] * work_excess + S["c_s"] * co2_head
                       + S["d_s"] * t / DAYS - S["e_s"] * counter - 0.6 * extra_mood + rng.normal(0, N["sd_stress"]))
        mood = int(np.clip(round(true_mood + bias), 1, 5))
        stress = int(np.clip(round(true_stress - bias), 1, 5))
        support = int(a == "A4" and t == 160)
        recent_moods.append(mood)

        add(a, t, "R02e", "mood", mood, "score_1_5")
        add(a, t, "R02e", "stress", stress, "score_1_5")
        add(a, t, "R02e", "support_requested", support, "bool")
        add(a, t, "R02e", "family_contact", fam, "bool")
        add(a, t, "R02e", "leisure_minutes", leisure, "min")

        # cognition (true every day; reported only on session days)
        med_effect = 1 if any(medical[(a, x)] == 1 for x in range(max(1, t - C["medical_effect_days"]), t + 1)) else 0
        slow = 1.2 * min(1, max(0, (t - 100) / 70)) if a == "A3" and 100 <= t <= 170 else (1.2 if a == "A3" and t > 170 else 0)
        true_cog = ability - C["f"] * sleep_debt - C["g"] * med_effect - slow + rng.normal(0, N["sd_cog"])
        if t in session_days:
            z = (min(true_cog, C["ceiling_z"]) - pre_mean) / pre_sd
            add(a, t, "R02", "cognitive_score_z", round(z, 2), "z", "simulator:winscat_like")

        # support sessions
        if t % SES["ppc_every_days"] == 0:
            held = 0 if (a == "A4" and 140 <= t <= 154) else 1        # scenario 6: missed PPC
            add(a, t, "R02c", "ppc_held", held, "bool")
            if held:
                low = np.mean(recent_moods[-7:]) < mood_base - 1
                p = SES["concern_raised_prob_when_low_mood"] if low else SES["concern_raised_prob_normal"]
                add(a, t, "R02c", "ppc_concern_raised", int(rng.random() < p), "bool")
        if t % SES["pmc_every_days"] == 0:
            add(a, t, "R02d", "pmc_held", 1, "bool")

        truth.append({"astronaut_id": a, "mission_day": int(t), "true_mood": round(true_mood, 3),
                      "true_stress": round(true_stress, 3), "true_cognition": round(true_cog, 3),
                      "sleep_debt": round(sleep_debt, 2), "co2_headache_day": co2_head})

# ------------------------------------------------------------------ scenario labels
label("A2", "R02e", "1_gradual_decline", 67, 75, "orange")
label("A3", "R02e", "2_sudden_drop", 40, 42, "yellow")
label("A2", "R02e", "3_underreporting", 120, 135, "model_only")
label("A4", "R02e", "4_co2_headache_mood", 80, 84, "linked")
label("A4", "R02e", "5_support_requested", 160, 160, "red")
label("A4", "R02c", "6_countermeasure_gap", 140, 154, "yellow")
label("A2", "R02", "7_post_event_cognition", 96, 96, "orange")
label("A3", "R02", "8_ceiling_effect", 100, 170, "pvt_only")

# ------------------------------------------------------------------ write
pd.DataFrame(readings).to_csv(f"{OUT}/behavior_readings.csv", index=False)
pd.DataFrame(truth).to_csv(f"{OUT}/behavior_truth.csv", index=False)
lab_path = f"{OUT}/anomaly_labels.csv"
new = pd.DataFrame(labels)
if os.path.exists(lab_path):
    old = pd.read_csv(lab_path)
    old = old[~old.indicator_id.astype(str).str.startswith("R02")]
    new = pd.concat([old, new], ignore_index=True)
new.to_csv(lab_path, index=False)

r = pd.DataFrame(readings)
print(f"behavior_readings.csv: {len(r):,} rows | metrics: {sorted(r.metric.unique())}")
print(f"anomaly_labels.csv: {len(labels)} R02 rows ({sum(l['is_decoy'] for l in labels)} decoys)")
if stubs_used:
    print("WARNING – stub drivers used (generate these modules first for real links):", ", ".join(stubs_used))
