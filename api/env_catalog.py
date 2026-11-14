"""
Environment metric catalog: what POST /environment accepts (raw telemetry, not daily values).

Ranges are physical sanity limits (team design), NOT alert thresholds: alerts come from rules.json.
NASA-STD-3001 Vol 2 Rev F [V2 6020] (p58) requires the vehicle to record pressure, humidity,
temperature, ppO2 and ppCO2 automatically; this list holds those plus the radiation dose rates.
"""

ENV_METRICS = {
    # metric                      indicator  unit       min   max
    "co2_ppm":                   ("R03c", "ppm",      100,  20000),
    "temp_c":                    ("R01g", "degC",     -10,  50),
    "rh_pct":                    ("R01g", "%",        0,    100),
    "cabin_pressure_mmhg":       ("R03c", "mmHg",     0,    1100),   # used for ppm -> mmHg if sent
    "ppo2_mmhg":                 (None,   "mmHg",     0,    1100),   # stored only; no rule yet
    "absorbed_dose_rate_uGy_h":  ("R21",  "uGy/h",    0,    1e6),    # area detector (RadLab DosTel1)
    "dose_eq_rate_uSv_h":        ("R21",  "uSv/h",    0,    1e7),    # area detector (RadLab ALTEA)
}


def check_env(metric, value, unit):
    """Return (indicator_id, None) if valid, else (None, reason)."""
    spec = ENV_METRICS.get(metric)
    if spec is None:
        return None, f"unknown environment metric '{metric}'"
    ind, u, lo, hi = spec
    if unit != u:
        return None, f"unit '{unit}' for {metric}; expected '{u}'"
    if not (lo <= value <= hi):
        return None, f"{metric}={value} outside plausible range {lo}–{hi}"
    return ind, None
