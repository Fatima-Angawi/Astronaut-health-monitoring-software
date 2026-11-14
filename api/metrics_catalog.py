"""
Metric catalog: which metrics the API accepts, their indicator, unit and a plausible range.

A reading whose metric is not here, whose unit differs, or whose value is outside the range is rejected.
Ranges are physical sanity limits (team design), NOT alert thresholds: alerts come from rules.json.
Add a metric here when a new device or indicator is added.
"""

METRICS = {
    # metric                 indicator  unit         min    max     note
    "sleep_h":              ("R01",  "h",          0,     24),     # V001
    "work_hours":           ("R01f", "h",          0,     24),
    "pvt_lapses":           ("R01c", "count",      0,     500),
    "pvt_slowest10_ms":     ("R01c", "ms",         100,   10000),
    "pvt_mean_rt_ms":       ("R01c", "ms",         100,   10000),
    "kss":                  ("R01d", "score_1_9",  1,     9),       # scale to verify (V020)
    "heart_rate":           ("R10b", "bpm",        20,    250),     # live watch readings
    "hr_resting":           ("R10b", "bpm",        20,    250),     # daily resting value
    "bp_systolic":          ("R10b", "mmHg",       50,    260),
    "bp_diastolic":         ("R10b", "mmHg",       20,    160),
    "spo2":                 ("R06b", "%",          50,    100),
    "symptom_logged":       ("R06",  "bool",       0,     1),
    "headache":             ("R06",  "bool",       0,     1),
    "medical_event":        ("R06",  "bool",       0,     1),
    "co2_1h_max_ppm":       ("R03c", "ppm",        100,   20000),   # V066 (1-hour average)
    "mood":                 ("R02e", "score_1_5",  1,     5),
    "stress":               ("R02e", "score_1_5",  1,     5),
    "support_requested":    ("R02e", "bool",       0,     1),
    "family_contact":       ("R02e", "bool",       0,     1),
    "leisure_minutes":      ("R02e", "min",        0,     1440),
    "exercise_minutes":     ("R02e", "min",        0,     1440),    # also used by R18 (bone); features read by metric name
    "cognitive_score_z":    ("R02",  "z",          -10,   10),
    "ppc_held":             ("R02c", "bool",       0,     1),
    "ppc_concern_raised":   ("R02c", "bool",       0,     1),
    "pmc_held":             ("R02d", "bool",       0,     1),
    "personal_dose_mSv":    ("R21",  "mSv",        0,     100),     # personal dosimeter, dose for that day
    "career_dose_before_mission_mSv": ("R21", "mSv", 0, 2000),   # dose before this mission, sent once on day 1
    # bone (R18): in-flight inputs + post-flight DXA; sanity ranges are team design
    "exercise_load_x_bw":   ("R18", "x_bw",  0, 5),
    "vitamin_d_taken":      ("R18", "bool",  0, 1),
    "fall_or_impact_event": ("R18", "bool",  0, 1),
    "body_weight":          ("R18", "kg",    20, 250),
    "postflight_abmd_total_hip":    ("R18", "g/cm2", 0.3, 2.0),
    "postflight_abmd_lumbar_spine": ("R18", "g/cm2", 0.3, 2.0),
    "postflight_abmd_femoral_neck": ("R18", "g/cm2", 0.3, 2.0),
}

# symptom_<type> flags from the symptom checklist (Medical ER Table 2 order, V035)
for s in ["nasal_congestion", "back_pain", "space_motion_sickness", "insomnia", "headache"]:
    METRICS[f"symptom_{s}"] = ("R06", "bool", 0, 1)


def as_markdown(catalog):
    """Catalog as a table for the API docs page (/docs), so the published contract always matches the code."""
    lines = ["| metric | unit | accepted range |", "|---|---|---|"]
    lines += [f"| `{m}` | `{u}` | {lo:g} to {hi:g} |" for m, (_, u, lo, hi) in catalog.items()]
    return "\n".join(lines)


def check(metric, value, unit):
    """Return (indicator_id, None) if valid, else (None, reason)."""
    spec = METRICS.get(metric)
    if spec is None:
        return None, f"unknown metric '{metric}'"
    ind, u, lo, hi = spec
    if unit != u:
        return None, f"unit '{unit}' for {metric}; expected '{u}'"
    if not (lo <= value <= hi):
        return None, f"{metric}={value} outside plausible range {lo}–{hi}"
    return ind, None
