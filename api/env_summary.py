"""
Server-side daily summary of environment telemetry: env_readings -> env_daily.

Runs inside the API after every POST /environment batch, for the dates that batch touched, so it
works the same for a replay feed (eda.py) and for live vehicle telemetry. Moved here from eda.py.

Method (Evidence and Decision Log, "Cabin environment"):
  - CO2: rolling 1-hour mean, because NASA-STD-3001 Vol 2 Rev F [V2 6004] (p51) limits "the average
    one-hour CO2 partial pressure" to 3 mmHg (V066). Daily alert value = highest 1-hour mean.
  - ppm -> mmHg uses the day's mean cabin pressure if the feed sends it, else 760 mmHg (ASSUMPTION, V046).
  - Temperature / humidity: daily mean (V065) and sleep-window mean (V053, BMed ER p63).
    Sleep window 21:30-06:00 UTC, counted on the wake-up date = TEAM DESIGN.
  - Area radiation: dose rate integrated over the day (trapezoid over consecutive readings; gaps longer
    than 3x the usual step are not bridged), then scaled to 24 h by the covered time = TEAM DESIGN (V064).
  - coverage_pct = readings received / readings expected; complete = coverage >= 80 % (team design).
    A partial day is still written, so a live CO2 peak alerts before the day ends.
  - If one source has several sensors for a metric, they are averaged per timestamp.
  - Days with low coverage are still scaled to 24 h; the engine must use complete = 1 rows
    for baselines and dose totals.
"""
import pandas as pd

CABIN_PRESSURE_MMHG = 760          # ASSUMPTION (V046), used only when no pressure is sent
MIN_HOUR_COVERAGE = 0.75           # a 1-hour mean needs >= 75 % of its readings (team design)
DAY_COMPLETE = 0.80                # team design
SLEEP_START_H, SLEEP_END_H = 21.5, 6.0   # team design: sleep window 21:30-06:00 UTC
GAP_FACTOR = 3                     # team design: radiation is not integrated across gaps > 3x the usual step


def _step(s):
    d = s.index.to_series().diff().dropna()
    d = d[d > pd.Timedelta(0)]
    return d.median() if len(d) else pd.Timedelta("1min")   # team design: fallback when only one reading exists


def _coverage(s, step, day):
    n = s[(s.index >= day) & (s.index < day + pd.Timedelta("1D"))].count()
    return min(100.0, round(n / (pd.Timedelta("1D") / step) * 100, 1))


def _dose_day(s, step, day):
    s = s[(s.index >= day) & (s.index < day + pd.Timedelta("1D"))].dropna()
    if len(s) < 2:
        return None, 0.0
    dt = s.index.to_series().diff().dt.total_seconds().iloc[1:] / 3600       # hours
    ok = dt <= step.total_seconds() / 3600 * GAP_FACTOR
    area = ((s.values[1:] + s.values[:-1]) / 2 * dt.values)[ok.values].sum()
    covered = dt[ok].sum()
    return (area * 24 / covered if covered else None), covered / 24


def summarize(con, source, dates):
    """Recompute env_daily for one source and the given UTC dates (YYYY-MM-DD)."""
    out = []
    for d in sorted(set(dates)):
        day = pd.Timestamp(d)
        # previous evening for sleep / rolling. 3h = team design: covers 21:30 sleep start and the 1-h CO2 window
        lo, hi = day - pd.Timedelta("3h"), day + pd.Timedelta("1D")
        raw = pd.read_sql_query(
            "SELECT time, metric, value, mission_day, is_real FROM env_readings "
            "WHERE source = ? AND time >= ? AND time < ?", con,
            params=(source, lo.strftime("%Y-%m-%dT%H:%M:%SZ"), hi.strftime("%Y-%m-%dT%H:%M:%SZ")))
        if raw.empty:
            continue
        raw["time"] = pd.to_datetime(raw["time"]).dt.tz_localize(None)
        today = raw[raw["time"] >= day]
        md = today["mission_day"].dropna()
        mission_day = int(md.max()) if len(md) else None
        if mission_day is None:                                               # live mission: look up the calendar
            r = con.execute("SELECT mission_day FROM mission_timeline WHERE date = ?", (d,)).fetchone()
            mission_day = r[0] if r else None
        is_real = int(raw["is_real"].min())
        series = {m: g.groupby("time")["value"].mean().sort_index() for m, g in raw.groupby("metric")}

        def add(metric, value, unit, value_id, cov):
            if value is not None and pd.notna(value):
                out.append((d, mission_day, metric, round(float(value), 3), unit, source, value_id,
                            is_real, cov, int(cov >= DAY_COMPLETE * 100)))

        hour_of = lambda idx: idx.hour + idx.minute / 60
        if "co2_ppm" in series:
            s = series["co2_ppm"]; st = _step(s); cov = _coverage(s, st, day)
            roll = s.rolling("60min", min_periods=max(1, int(pd.Timedelta("1h") / st * MIN_HOUR_COVERAGE))).mean()
            peak = roll[roll.index >= day].max()
            p = series.get("cabin_pressure_mmhg")
            pressure = p[p.index >= day].mean() if p is not None and p[p.index >= day].count() else CABIN_PRESSURE_MMHG
            add("co2_1h_max_ppm", peak, "ppm", "V066", cov)
            add("co2_1h_max_mmhg", peak * pressure / 1e6 if pd.notna(peak) else None, "mmHg", "V066", cov)
            add("co2_daily_mean_ppm", s[s.index >= day].mean(), "ppm", "V065", cov)
        for raw_m, mean_m, sleep_m in [("temp_c", "temp_daily_mean_c", "temp_sleep_mean_c"),
                                       ("rh_pct", "rh_daily_mean_pct", "rh_sleep_mean_pct")]:
            if raw_m in series:
                s = series[raw_m]; st = _step(s); cov = _coverage(s, st, day)
                unit = "degC" if raw_m == "temp_c" else "%"
                add(mean_m, s[s.index >= day].mean(), unit, "V065", cov)
                h = hour_of(s.index)
                night = s[((s.index < day) & (h >= SLEEP_START_H)) | ((s.index >= day) & (h < SLEEP_END_H))]
                add(sleep_m, night.mean() if len(night) else None, unit, "V053", cov)
        for raw_m, day_m, unit in [("absorbed_dose_rate_uGy_h", "absorbed_dose_uGy_day", "uGy/day"),
                                   ("dose_eq_rate_uSv_h", "dose_eq_uSv_day", "uSv/day")]:
            if raw_m in series:
                s = series[raw_m]; st = _step(s)
                dose, frac = _dose_day(s, st, day)
                add(day_m, dose, unit, "V064", round(frac * 100, 1))

    con.executemany("INSERT OR REPLACE INTO env_daily VALUES (?,?,?,?,?,?,?,?,?,?)", out)
    return len(out)
