"""
Engine step 1: features. Turns everything stored in health.db into one set of numbers per astronaut per
mission day, named exactly as the metrics in rules.json, plus the personal baselines.

Reads:  readings (live only), env_daily, spe_events/spe_channels, mission_timeline, mission_events, crew
Writes: daily_features (astronaut_id, mission_day, metric, value)  – long format, rebuilt on every run
        baselines      (astronaut_id, indicator_id, metric, median, robust_sd, n_points, computed_from)
Never reads anomaly_labels or any *_truth file.

Every threshold-like number below is a Value ID or TEAM DESIGN; the alert thresholds themselves live in
rules.json and are applied by rules.py, not here.

Usage: python engine/features.py
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"

BASELINE_DAYS = (1, 14)            # TEAM DESIGN: first two in-flight weeks, before the first docking week (27–30)
MAD_TO_SD = 1.4826                 # robust SD = 1.4826 x MAD (normal-consistent)
MIN_SD = {                         # TEAM DESIGN: floor so a very steady person is not flagged by tiny changes
    "pvt_lapses": 2.0, "pvt_slowest10_ms": 30.0, "hr_resting": 2.0, "mood": 0.5, "kss": 0.5,
    "exercise_minutes": 5.0, "sleep_h": 0.3, "work_hours": 0.5, "stress": 0.5,
}
BASELINE_METRICS = {"pvt_lapses": "R01c", "pvt_slowest10_ms": "R01c", "hr_resting": "R10b",
                    "mood": "R02e", "kss": "R01d", "exercise_minutes": "R18",
                    "sleep_h": "R01", "work_hours": "R01f", "stress": "R02e"}
RATING_SCALES = {"mood", "stress", "kss"}   # TEAM DESIGN: whole-number ratings; their median moves in whole steps,
                                            # so the baseline centre is the mean (e.g. 4.6, not 5)
PVT_BAD_WINDOW, PVT_BAD_MIN = 3, 2  # TEAM DESIGN: one noisy PVT day is not a pattern
SUM_METRICS = {"personal_dose_mSv", "exercise_minutes", "leisure_minutes"}   # several readings a day are added up
SHORT_SLEEP_H = 6                  # R01 yellow value (V008), reused for the sleep-environment link (TEAM DESIGN)
SLEEP_ENV = {"temp_sleep_mean_c": (17, 28), "rh_sleep_mean_pct": (40, 60)}   # V053 (BMed ER p63)
CO2_HEADACHE_MMHG = 2.5            # V045
CABIN_PRESSURE_MMHG = 760          # ASSUMPTION (V046), only for simulated CO2 sent in ppm per astronaut
SPE_ACTIVE_DAYS = 2                # TEAM DESIGN: onset day + next day (DONKI gives onset only)
EVA_PLANNED_AHEAD = 3              # TEAM DESIGN: an EVA in the next 3 days counts as "planned"
BMD_RATES = {                      # %/month, Fracture ER Table 4 p22; hip and femoral neck use trochanter (ASSUMPTION)
    "ared":     {"hip": -0.5,  "femoral_neck": -0.5,  "spine": -0.32},
    "pre_ared": {"hip": -1.56, "femoral_neck": -1.56, "spine": -1.06},
}
DAYS_PER_MONTH = 30.44
ADHERENCE = 0.75                   # TEAM DESIGN: 7-day mean exercise >= 75 % of own baseline median
SLEEP_MIN_DAYS = 5                 # TEAM DESIGN: the 7-day sleep mean needs at least 5 of the 7 nights
MIN_BASELINE_POINTS = 3            # TEAM DESIGN: no baseline from fewer than 3 days


def load(con):
    tl = pd.read_sql("SELECT mission_day, date, replay_date FROM mission_timeline ORDER BY mission_day", con)
    if tl.empty:
        raise SystemExit("mission_timeline is empty: run inputs/load_db.py first")
    r = pd.read_sql("SELECT astronaut_id, time, mission_day, metric, value FROM readings "
                    "WHERE availability = 'live'", con)
    by_date = dict(zip(tl.date, tl.mission_day))
    miss = r.mission_day.isna()                                   # real devices may not send mission_day
    r.loc[miss, "mission_day"] = r.loc[miss, "time"].str[:10].map(by_date)
    r = r.dropna(subset=["mission_day"])
    r["mission_day"] = r.mission_day.astype(int)
    return tl, r


def daily_wide(r, days):
    agg = r.groupby(["astronaut_id", "mission_day", "metric"]).value
    w = pd.concat([agg.sum()[agg.sum().index.get_level_values("metric").isin(SUM_METRICS)],
                   agg.mean()[~agg.mean().index.get_level_values("metric").isin(SUM_METRICS)]]).unstack("metric")
    crew = sorted(r.astronaut_id.unique())
    full = pd.MultiIndex.from_product([crew, days], names=["astronaut_id", "mission_day"])
    return w.reindex(full)


def baselines(w):
    out, lo, hi = [], *BASELINE_DAYS
    for (a, ind), m in [((a, ind), m) for a in w.index.get_level_values(0).unique()
                        for m, ind in BASELINE_METRICS.items()]:
        if m not in w:
            continue
        x = w.loc[a, m].loc[lo:hi].dropna()
        if len(x) < MIN_BASELINE_POINTS:
            continue
        med = float(x.mean()) if m in RATING_SCALES else float(x.median())
        sd = max(MAD_TO_SD * float((x - x.median()).abs().median()), MIN_SD[m])
        out.append({"astronaut_id": a, "indicator_id": ind, "metric": m, "median": med,
                    "robust_sd": sd, "n_points": len(x),
                    "computed_from": f"mission_day {lo}-{hi}" + (" (mean: rating scale)" if m in RATING_SCALES else "")})
    return pd.DataFrame(out)


def main():
    con = sqlite3.connect(DB, timeout=30)
    if not con.execute("SELECT 1 FROM readings WHERE availability = 'live' LIMIT 1").fetchone():
        with con:                                             # live mode starts with an empty database
            con.execute("DELETE FROM daily_features")
            con.execute("DELETE FROM baselines")
        print("no readings yet")
        con.close()
        return
    tl, r = load(con)
    last_day = int(tl.mission_day.max())                      # the mission's last day (projections look ahead to it)
    have = r.mission_day[r.mission_day >= 1]
    if have.empty:
        with con:
            con.execute("DELETE FROM daily_features")
            con.execute("DELETE FROM baselines")
        print("no readings yet")
        con.close()
        return
    # only days that have data: forward-filled exercise and the cumulative bone and dose features would otherwise
    # produce values, and alerts, for days that have not happened yet
    days = [d for d in tl.mission_day if d <= have.max()]
    w = daily_wide(r, days)
    base = baselines(w)
    b = {(x.astronaut_id, x.metric): x for x in base.itertuples()}
    f = pd.DataFrame(index=w.index)

    def per_person(fn):
        return pd.concat([fn(a, w.loc[a]) for a in w.index.get_level_values(0).unique()])

    def keyed(a, s):
        s.index = pd.MultiIndex.from_product([[a], s.index], names=["astronaut_id", "mission_day"])
        return s

    # --- direct daily values (rules compare these as they are, or against baselines)
    for m in ["sleep_h", "work_hours", "pvt_lapses", "pvt_slowest10_ms", "kss", "hr_resting", "spo2",
              "mood", "support_requested", "symptom_logged", "cognitive_score_z", "exercise_minutes"]:
        if m in w:
            f[m] = w[m]
    for m in BASELINE_METRICS:                                    # z vs personal baseline, for baseline ops
        if m in w:
            f[f"{m}_z"] = per_person(lambda a, x: keyed(a, (x[m] - b[(a, m)].median) / b[(a, m)].robust_sd)
                                     if (a, m) in b else keyed(a, x[m] * np.nan))

    # --- R01 / R01f windows
    if "sleep_h" in w:
        f["sleep_h_7d_mean"] = per_person(lambda a, x: keyed(a, x.sleep_h.rolling(7, min_periods=SLEEP_MIN_DAYS).mean()))
    if "work_hours" in w:
        f["work_hours_7d_sum"] = per_person(lambda a, x: keyed(a, x.work_hours.rolling(7, min_periods=7).sum()))
        f["work_days_10h_7d"] = per_person(lambda a, x: keyed(a, (x.work_hours >= 10).astype(float)
                                                              .rolling(7, min_periods=7).sum()))

    # --- R01d: PVT worse than baseline + 2 SD on 2 of the last 3 days while KSS is not above own baseline (TEAM DESIGN)
    if {"pvt_lapses_z", "pvt_slowest10_ms_z", "kss_z"} <= set(f):
        pvt_bad = ((f.pvt_lapses_z > 2) | (f.pvt_slowest10_ms_z > 2)).astype(float)
        pvt_bad_2of3 = pvt_bad.groupby(level=0).transform(lambda s: s.rolling(PVT_BAD_WINDOW, min_periods=1).sum()) >= PVT_BAD_MIN
        f["kss_pvt_mismatch"] = (pvt_bad_2of3 & (f.kss_z <= 0)).astype(float).where(f.kss_z.notna())

    # --- mission events: critical within 24 h, EVA today / planned
    ev = pd.read_sql("SELECT mission_day, astronaut_id, type, critical FROM mission_events", con)
    crew = w.index.get_level_values(0).unique()
    def event_days(a, crit=None, kind=None):
        e = ev[(ev.astronaut_id.isna()) | (ev.astronaut_id == a)]
        if crit is not None:
            e = e[e.critical == crit]
        if kind is not None:
            e = e[e.type == kind]
        return set(e.mission_day.astype(int))
    rows = []
    for a in crew:
        crit, eva = event_days(a, crit=1), event_days(a, kind="EVA")
        for d in days:
            rows.append({"astronaut_id": a, "mission_day": d,
                         "days_to_next_critical": min((c - d for c in crit if c >= d), default=np.nan),   # 0 = today
                         "eva_today": float(d in eva),
                         "eva_planned": float(any(d + k in eva for k in range(1, EVA_PLANNED_AHEAD + 1)))})
    f = f.join(pd.DataFrame(rows).set_index(["astronaut_id", "mission_day"]))

    # --- cabin: env_daily (real) first, else the simulated per-astronaut CO2
    env = pd.read_sql("SELECT mission_day, metric, value, complete FROM env_daily WHERE mission_day IS NOT NULL", con)
    co2_env = env[env.metric == "co2_1h_max_mmhg"].groupby("mission_day").value.max()      # partial days allowed
    sleep_env = env[(env.complete == 1) & env.metric.isin(SLEEP_ENV)].pivot_table(
        index="mission_day", columns="metric", values="value", aggfunc="mean")
    md = f.index.get_level_values("mission_day")
    sim_co2 = (w["co2_1h_max_ppm"] * CABIN_PRESSURE_MMHG / 1e6) if "co2_1h_max_ppm" in w else pd.Series(np.nan, index=w.index)
    f["co2_1h_max_mmhg"] = pd.Series(md.map(co2_env), index=f.index).fillna(sim_co2)
    if "headache" in w:
        f["co2_headache_day"] = ((f.co2_1h_max_mmhg > CO2_HEADACHE_MMHG) & (w.headache == 1)).astype(float)
    if not sleep_env.empty and "sleep_h" in w:
        out = pd.Series(False, index=f.index)
        for m, (lo, hi) in SLEEP_ENV.items():
            if m in sleep_env:
                v = pd.Series(md.map(sleep_env[m]), index=f.index)
                out |= (v < lo) | (v > hi)
        f["env_out_of_range_short_sleep"] = (out & (w.sleep_h < SHORT_SLEEP_H)).astype(float)

    # --- R21b: SPE active (DONKI onset mapped by replay date, else calendar date)
    spe = pd.read_sql("SELECT e.event_key, e.onset_time, MAX(c.min_energy_mev) AS mev FROM spe_events e "
                      "JOIN spe_channels c USING (event_key) GROUP BY e.event_key", con)
    day_of = {**dict(zip(tl.date, tl.mission_day)), **dict(zip(tl.replay_date.dropna(), tl.mission_day))}
    active = {}
    for e in spe.itertuples():
        d0 = day_of.get(e.onset_time[:10])
        if d0 is None:
            continue
        for d in range(d0, d0 + SPE_ACTIVE_DAYS):
            active[d] = max(active.get(d, 0), e.mev)
    f["spe_active"] = pd.Series(md.map(lambda d: float(d in active)), index=f.index)
    f["spe_channel_min_mev"] = pd.Series(md.map(lambda d: active.get(d, np.nan)), index=f.index)
    f["spe_active_eva_planned"] = ((f.spe_active == 1) & (f.eva_planned == 1)).astype(float)
    f["spe_active_eva_in_progress"] = ((f.spe_active == 1) & (f.eva_today == 1)).astype(float)

    # --- R21: projected career dose = before mission + received so far + mean daily so far x days left (TEAM DESIGN)
    if "personal_dose_mSv" in w:
        prior = r[r.metric == "career_dose_before_mission_mSv"].groupby("astronaut_id").value.max()
        def career(a, x):
            dose = x.personal_dose_mSv.fillna(0)
            cum, n = dose.cumsum(), pd.Series(range(1, len(dose) + 1), index=dose.index)
            return keyed(a, prior.get(a, 0) + cum + cum / n * (last_day - dose.index))
        f["projected_career_dose_msv"] = per_person(career)
        f["career_dose_msv"] = per_person(lambda a, x: keyed(a, prior.get(a, 0) + x.personal_dose_mSv.fillna(0).cumsum()))   # actual so far

    # --- R18: projected % of preflight BMD, rate chosen per day by exercise adherence
    if "exercise_minutes" in w:
        def bmd(a, x):
            if (a, "exercise_minutes") not in b:
                return pd.DataFrame(index=keyed(a, x.exercise_minutes).index)
            ex7 = x.exercise_minutes.ffill().rolling(7, min_periods=1).mean()
            adherent = ex7 >= ADHERENCE * b[(a, "exercise_minutes")].median
            out = {}
            for site in ["hip", "spine", "femoral_neck"]:
                rate = np.where(adherent, BMD_RATES["ared"][site], BMD_RATES["pre_ared"][site]) / DAYS_PER_MONTH
                out[f"projected_bmd_pct_{site}"] = 100 + np.cumsum(rate)
            # gap to the path of a fully adherent astronaut (ARED rate every day): 0 = on the normal path
            path = 100 + np.cumsum(np.full(len(x), BMD_RATES["ared"]["hip"] / DAYS_PER_MONTH))
            out["projected_bmd_hip_gap"] = out["projected_bmd_pct_hip"] - path
            df = pd.DataFrame(out, index=x.index)
            df.index = pd.MultiIndex.from_product([[a], df.index], names=["astronaut_id", "mission_day"])
            return df
        f = f.join(pd.concat([bmd(a, w.loc[a]) for a in crew]))

    # --- write
    long = f.reset_index().melt(id_vars=["astronaut_id", "mission_day"], var_name="metric").dropna(subset=["value"])
    with con:
        con.execute("DELETE FROM daily_features")
        long.to_sql("daily_features", con, if_exists="append", index=False)
        con.execute("DELETE FROM baselines")
        base.to_sql("baselines", con, if_exists="append", index=False)
    print(f"daily_features: {len(long):,} rows, {long.metric.nunique()} metrics, "
          f"{f.index.get_level_values(0).nunique()} astronauts x {len(days)} days | baselines: {len(base)}")
    print("SPE active days:", sorted(active), "| real CO2 days from env_daily:", len(co2_env))
    con.close()


if __name__ == "__main__":
    main()
