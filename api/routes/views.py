"""
Read endpoints for the UI: what the engine has already computed, as JSON.

Rules:
  - read-only, except the two acknowledge endpoints; nothing here runs the engine or changes data otherwise
  - never reads anomaly_labels or any *_truth file
  - list endpoints return {"ok": true, "count": n, "items": [...]}; rows keep the tables' column names
  - unknown astronaut / day / id -> HTTP 404 with {"ok": false, "error": "..."}
The demo is a replay, so the UI chooses a "current mission day" and asks for that day.
"""
import math
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from api.db import connect, state_get, state_set

router = APIRouter(tags=["UI views"])
LEVELS = ["yellow", "orange", "red"]
ALERT_COLS = ("a.alert_id, a.astronaut_id, a.time, t.mission_day, a.indicator_id, a.level, a.source_engine, "
              "a.rule_id, a.reason, a.action, a.value_ids, a.escalated_to, a.acknowledged, a.synced_to_ground")
ALERT_FROM = "FROM alerts a LEFT JOIN mission_timeline t ON t.date = substr(a.time, 1, 10)"
MODEL = "MODEL"            # alert_episodes names the anomaly model's alerts 'MODEL'; in alerts their indicator_id is NULL


def rows(sql, params=()):
    con = connect()
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(sql, params)]
    finally:
        con.close()


def items(found, **extra):
    return {"ok": True, "count": len(found), **extra, "items": found}


def error(status, message):
    return JSONResponse(status_code=status, content={"ok": False, "error": message})


def known_astronaut(a):
    return bool(rows("SELECT 1 FROM crew WHERE astronaut_id = ?", (a,)))


def known_day(d):
    return bool(rows("SELECT 1 FROM mission_timeline WHERE mission_day = ?", (d,)))


# ------------------------------------------------------------------ mission and crew
def clock_state():
    """The mission clock and the engine/replay status, from system_state."""
    con = connect()
    try:
        g = lambda k, d=None: state_get(con, k, d)
        return {"clock_running": g("clock_running", "0") == "1", "clock_day": int(g("clock_day", "0") or 0),
                "clock_started_at": g("clock_started_at", ""), "seconds_per_day": float(g("seconds_per_day", "60") or 60),
                "replay_sent_through": int(g("replay_sent_through", "0") or 0),
                "engine_last_run": g("engine_last_run"), "engine_last_status": g("engine_last_status"),
                "engine_runs": int(g("engine_runs", "0") or 0)}
    finally:
        con.close()


def last_mission_day():
    return rows("SELECT MAX(mission_day) AS d FROM mission_timeline")[0]["d"] or 0


def current_day(st=None, last=None):
    """Paused: the clock's day. Running: that day plus the whole mission days passed since it was started.
    Capped at the last mission day. 0 = the mission has not started."""
    st = st or clock_state()
    last = last_mission_day() if last is None else last
    day = st["clock_day"]
    if st["clock_running"] and st["clock_started_at"]:
        passed = (datetime.now(timezone.utc) - datetime.fromisoformat(st["clock_started_at"])).total_seconds()
        day += math.floor(passed / st["seconds_per_day"])
    return min(day, last)


@router.get("/mission", summary="Mission length, the mission clock and the engine status",
            description="""
The range of mission days and where the mission clock is, so the UI knows which day to show.

**Reply:** `days`, `first_day` and `last_day` (each `{"mission_day", "date"}`), and `latest_day_with_data`:
the highest mission day found in `triage_daily` or `daily_features` (null before the engine has run).

The clock: `current_day` (0 = not started; paused = the clock's day; running = the clock's day plus the days
passed since it was started, capped at the last day), `clock_running`, `seconds_per_day` (how long one mission
day lasts), and `replay_sent_through` (the last day whose data the replay has sent). Change it with
`POST /mission/clock`.

The engine: `engine_last_run` (UTC time), `engine_last_status` ("ok", or the failing step and its last output
lines), `engine_runs` (how many times it has run since the database was reset).

Example: `GET /mission`
""")
def mission():
    tl = rows("SELECT mission_day, date FROM mission_timeline ORDER BY mission_day")
    if not tl:
        return error(404, "mission_timeline is empty: run inputs/load_db.py first")
    latest = rows("SELECT MAX(d) AS d FROM (SELECT MAX(mission_day) AS d FROM triage_daily "
                  "UNION ALL SELECT MAX(mission_day) FROM daily_features)")[0]["d"]
    st = clock_state()
    return {"ok": True, "days": len(tl), "first_day": tl[0], "last_day": tl[-1], "latest_day_with_data": latest,
            "current_day": current_day(st, tl[-1]["mission_day"]), "clock_running": st["clock_running"],
            "seconds_per_day": st["seconds_per_day"], "replay_sent_through": st["replay_sent_through"],
            "engine_last_run": st["engine_last_run"], "engine_last_status": st["engine_last_status"],
            "engine_runs": st["engine_runs"]}


class ClockAction(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"action": "set_day", "day": 60}]})
    action: str = Field(description="start, pause, set_day, set_speed or replay_progress.")
    day: Optional[int] = Field(None, description="For set_day: the day to jump to (0 = before the mission). "
                                                 "For replay_progress: the last day the replay has sent.")
    seconds_per_day: Optional[float] = Field(None, description="For set_speed: seconds one mission day lasts (> 0).")


@router.post("/mission/clock", summary="Start, pause or move the mission clock",
             description="""
Controls the demo's mission clock. One of:

- `{"action": "start"}` : the clock runs from the current day
- `{"action": "pause"}` : the clock stops at the current day
- `{"action": "set_day", "day": 60}` : jump to a day (0 to the last day). The replay then sends any days up to it
  that were not sent yet; jumping back only changes which day is shown
- `{"action": "set_speed", "seconds_per_day": 10}` : change how long a mission day lasts; the current day is kept
- `{"action": "replay_progress", "day": 12}` : used by `inputs/replay.py` to record the last day it has sent

**Reply:** the new `GET /mission` body. HTTP 400 for an unknown action or an out-of-range value.
""")
def mission_clock(body: ClockAction):
    last = last_mission_day()
    if body.action == "set_day" and (body.day is None or not 0 <= body.day <= last):
        return error(400, f"set_day needs a day between 0 and {last}")
    if body.action == "replay_progress" and (body.day is None or not 0 <= body.day <= last):
        return error(400, f"replay_progress needs a day between 0 and {last}")
    if body.action == "set_speed" and (body.seconds_per_day is None or body.seconds_per_day <= 0):
        return error(400, "set_speed needs seconds_per_day greater than 0")
    if body.action not in ("start", "pause", "set_day", "set_speed", "replay_progress"):
        return error(400, "action must be start, pause, set_day, set_speed or replay_progress")
    st = clock_state()
    now = datetime.now(timezone.utc).isoformat()
    cur = current_day(st, last)
    con = connect()
    try:
        with con:
            if body.action == "start":
                if not st["clock_running"]:
                    state_set(con, clock_running=1, clock_started_at=now)
            elif body.action == "pause":
                state_set(con, clock_running=0, clock_day=cur)
            elif body.action == "set_day":
                state_set(con, clock_day=body.day, clock_started_at=now)
            elif body.action == "set_speed":
                state_set(con, clock_day=cur, clock_started_at=now, seconds_per_day=body.seconds_per_day)
            else:
                state_set(con, replay_sent_through=body.day)
    finally:
        con.close()
    return mission()


@router.get("/crew", summary="The crew list",
            description="Each astronaut's `astronaut_id` and `role` ('CMO' = crew medical officer). "
                        "Preflight medical values are not included.\n\nExample: `GET /crew`")
def crew():
    return items(rows("SELECT astronaut_id, role FROM crew ORDER BY astronaut_id"))


@router.get("/events", summary="Planned mission events (EVAs, dockings, landing)",
            description="""
Rows of `mission_events` with the `date` of each, in day order. With `astronaut_id`, that astronaut's own
events plus the crew-wide ones (`astronaut_id` null). `critical` = 1 marks the events the red sleep and PVT
rules look ahead to. `days_until` counts from `from_day` (0 = that day).

Example: `GET /events?astronaut_id=A2&from_day=66` (the "next EVA" card: take the first item of type EVA)
""")
def events(
    astronaut_id: Optional[str] = Query(None, description="e.g. A2: that astronaut's events and crew-wide events."),
    from_day: int = Query(1, description="Only events on or after this mission day."),
    to_day: int = Query(100000, description="Only events on or before this mission day (default: to the end)."),
):
    if astronaut_id is not None and not known_astronaut(astronaut_id):
        return error(404, f"unknown astronaut '{astronaut_id}'")
    who = "AND (e.astronaut_id IS NULL OR e.astronaut_id = ?)" if astronaut_id is not None else ""
    return items(rows(f"SELECT e.event_id, e.mission_day, t.date, e.astronaut_id, e.type, e.start_time, e.end_time, "
                      f"e.critical, e.mission_day - ? AS days_until FROM mission_events e "
                      f"LEFT JOIN mission_timeline t USING (mission_day) "
                      f"WHERE e.mission_day BETWEEN ? AND ? {who} ORDER BY e.mission_day, e.event_id",
                      [from_day, from_day, to_day] + ([astronaut_id] if astronaut_id is not None else [])))


# ------------------------------------------------------------------ one astronaut, one day: everything for the main screen
SUMMARY_CARDS = ["pvt_lapses", "sleep_h_7d_mean", "mood"]       # TEAM DESIGN: the measures shown as cards


@router.get("/summary", summary="One astronaut on one day: the main screen in one call",
            description="""
Everything the main screen needs for one astronaut on one mission day:

- `status`: that day's row of `triage_daily` (level, standing level, who it goes to), as in `GET /status`
- `cards`: for `pvt_lapses`, `sleep_h_7d_mean` and `mood`, the latest value on or before that day (with the
  day it is from) and the astronaut's personal `baseline` if the metric has one; `next_critical_event`:
  the next event with `critical` = 1 for this astronaut or the whole crew, with `days_until` (0 = today)
- `context`: `spe_active` and the highest channel reached; `cabin_co2` (highest 1-hour mean of the day in
  mmHg and in ppm, and whether it is real telemetry); `dose_today_msv`; `career_dose_msv` and
  `projected_career_dose_msv`

A value that does not exist for that day is null. Without `day` it uses the mission clock's current day
(day 0 = before the mission: everything empty). HTTP 404 for an unknown astronaut or day.

Example: `GET /summary?astronaut_id=A2&day=66`
""")
def summary(astronaut_id: str = Query(..., description="e.g. A2"),
            day: Optional[int] = Query(None, description="Mission day, e.g. 66. Default: the mission clock's "
                                                         "current day.")):
    if not known_astronaut(astronaut_id):
        return error(404, f"unknown astronaut '{astronaut_id}'")
    if day is None:
        day = current_day()
    tl = rows("SELECT date FROM mission_timeline WHERE mission_day = ?", (day,))
    if not tl and day != 0:
        return error(404, f"mission day {day} is not in the mission")
    a = astronaut_id

    def feature(metric, latest=False):
        op = "<=" if latest else "="
        r = rows(f"SELECT f.metric, f.value, f.mission_day, t.date FROM daily_features f "
                 f"LEFT JOIN mission_timeline t USING (mission_day) WHERE f.astronaut_id = ? AND f.metric = ? "
                 f"AND f.mission_day {op} ? ORDER BY f.mission_day DESC LIMIT 1", (a, metric, day))
        return r[0] if r else None

    cards = {}
    for m in SUMMARY_CARDS:
        card = feature(m, latest=True)
        if card:
            base = rows("SELECT median, robust_sd, computed_from FROM baselines WHERE astronaut_id = ? AND metric = ?", (a, m))
            card["baseline"] = base[0] if base else None
        cards[m] = card
    nxt = rows("SELECT e.event_id, e.mission_day, t.date, e.astronaut_id, e.type, e.start_time, e.end_time, e.critical, "
               "e.mission_day - ? AS days_until FROM mission_events e LEFT JOIN mission_timeline t USING (mission_day) "
               "WHERE e.critical = 1 AND e.mission_day >= ? AND (e.astronaut_id IS NULL OR e.astronaut_id = ?) "
               "ORDER BY e.mission_day LIMIT 1", (day, day, a))
    cards["next_critical_event"] = nxt[0] if nxt else None

    value = lambda m: (feature(m) or {}).get("value")
    real = rows("SELECT MAX(value) AS v FROM env_daily WHERE metric = 'co2_1h_max_ppm' AND mission_day = ?", (day,))[0]["v"]
    sim = rows("SELECT AVG(value) AS v FROM readings WHERE astronaut_id = ? AND metric = 'co2_1h_max_ppm' "
               "AND mission_day = ?", (a, day))[0]["v"]
    spe = value("spe_active")
    context = {
        "spe_active": None if spe is None else bool(spe),
        "spe_channel_min_mev": value("spe_channel_min_mev"),
        "cabin_co2": {"mmhg": value("co2_1h_max_mmhg"), "ppm": real if real is not None else sim,
                      "is_real": int(real is not None)},
        "dose_today_msv": rows("SELECT SUM(value) AS v FROM readings WHERE astronaut_id = ? AND "
                               "metric = 'personal_dose_mSv' AND mission_day = ?", (a, day))[0]["v"],
        "career_dose_msv": value("career_dose_msv"),
        "projected_career_dose_msv": value("projected_career_dose_msv"),
    }
    status_row = rows("""SELECT c.astronaut_id, c.role, ? AS mission_day,
                                COALESCE(t.level, 'none') AS level, t.escalated_to,
                                COALESCE(t.standing_level, 'none') AS standing_level, t.standing_escalated_to,
                                COALESCE(t.n_alerts, 0) AS n_alerts, t.indicators, t.top_reason,
                                COALESCE(t.model_flag, 0) AS model_flag
                         FROM crew c LEFT JOIN triage_daily t ON t.astronaut_id = c.astronaut_id AND t.mission_day = ?
                         WHERE c.astronaut_id = ?""", (day, day, a))[0]
    return {"ok": True, "astronaut_id": a, "mission_day": day, "date": tl[0]["date"] if tl else None,
            "status": status_row, "cards": cards, "context": context}


# ------------------------------------------------------------------ status of one day
@router.get("/status", summary="Everyone's level on one mission day",
            description="""
One item per astronaut for that mission day, from `triage_daily`: `level` (today's acute alerts) and
`standing_level` (slow conditions: career dose, bone projection), who each goes to, `n_alerts`, `indicators`,
`top_reason` and `model_flag`. An astronaut with nothing that day comes back with `level` "none",
`standing_level` "none" and `n_alerts` 0. Without `day` it uses the mission clock's current day (day 0 =
before the mission: everyone "none").

`cabin` lists the crew-wide episodes (`astronaut_id` = 'CREW', e.g. cabin CO2 or a solar particle event)
that cover that day.

Example: `GET /status?day=66`
""")
def status(day: Optional[int] = Query(None, description="Mission day, e.g. 66. Default: the mission clock's "
                                                         "current day.", examples=[66])):
    if day is None:
        day = current_day()
    tl = rows("SELECT mission_day, date FROM mission_timeline WHERE mission_day = ?", (day,))
    if not tl and day != 0:
        return error(404, f"mission day {day} is not in the mission")
    found = rows("""SELECT c.astronaut_id, c.role, ? AS mission_day,
                           COALESCE(t.level, 'none') AS level, t.escalated_to,
                           COALESCE(t.standing_level, 'none') AS standing_level, t.standing_escalated_to,
                           COALESCE(t.n_alerts, 0) AS n_alerts, t.indicators, t.top_reason,
                           COALESCE(t.model_flag, 0) AS model_flag
                    FROM crew c LEFT JOIN triage_daily t ON t.astronaut_id = c.astronaut_id AND t.mission_day = ?
                    ORDER BY c.astronaut_id""", (day, day))
    cabin = rows("SELECT * FROM alert_episodes WHERE astronaut_id = 'CREW' AND start_day <= ? AND end_day >= ? "
                 "ORDER BY start_day DESC", (day, day))
    return items(found, mission_day=day, date=tl[0]["date"] if tl else None, cabin=cabin)


# ------------------------------------------------------------------ episodes and alerts
@router.get("/episodes", summary="Alert episodes (consecutive alert days merged into one problem)",
            description="""
Rows of `alert_episodes` that cover a day (the mission clock's current day unless `day` is given). All
parameters are optional and combine. Sorted red first, then orange, yellow; within a level, the newest
`start_day` first.

Example: `GET /episodes?astronaut_id=A2&day=66&min_level=orange`
""")
def episodes(
    astronaut_id: Optional[str] = Query(None, description="Only this astronaut's episodes, e.g. A2 (or CREW)."),
    day: Optional[int] = Query(None, description="Only episodes that cover this mission day "
                                                 "(start_day <= day <= end_day). Default: the mission clock's "
                                                 "current day."),
    min_level: Optional[str] = Query(None, description="yellow, orange or red: that level and above."),
    open: int = Query(0, description="1 = only episodes not yet acknowledged."),
    include_cabin: int = Query(1, description="1 (default) = include crew-wide episodes (astronaut_id 'CREW'); "
                                              "0 = leave them out."),
):
    where, params = [], []
    if astronaut_id is not None:
        if astronaut_id != "CREW" and not known_astronaut(astronaut_id):
            return error(404, f"unknown astronaut '{astronaut_id}'")
        where.append("(astronaut_id = ?" + (" OR astronaut_id = 'CREW')" if include_cabin else ")"))
        params.append(astronaut_id)
    elif not include_cabin:
        where.append("astronaut_id != 'CREW'")
    if day is None:
        day = current_day()
    if day != 0 and not known_day(day):
        return error(404, f"mission day {day} is not in the mission")
    where.append("start_day <= ? AND end_day >= ?"); params += [day, day]
    if min_level is not None:
        if min_level not in LEVELS:
            return error(400, f"min_level must be one of {LEVELS}")
        keep = LEVELS[LEVELS.index(min_level):]
        where.append(f"level IN ({','.join('?' * len(keep))})"); params += keep
    if open:
        where.append("acknowledged = 0")
    sql = ("SELECT * FROM alert_episodes" + (" WHERE " + " AND ".join(where) if where else "")
           + " ORDER BY CASE level WHEN 'red' THEN 0 WHEN 'orange' THEN 1 ELSE 2 END, start_day DESC, astronaut_id")
    return items(rows(sql, params))


@router.get("/alerts", summary="Single alerts (one rule hit or one model flag on one day)",
            description="""
Rows of `alerts`, with `mission_day` worked out from the alert's date. At least one filter is required
(HTTP 400 otherwise). Use `indicator_id=MODEL` for the anomaly model's alerts, which have no indicator.

Example: `GET /alerts?astronaut_id=A2&day=66`
""")
def alerts(
    astronaut_id: Optional[str] = Query(None, description="Only this astronaut's alerts, e.g. A2."),
    day: Optional[int] = Query(None, description="Only alerts on this mission day."),
    indicator_id: Optional[str] = Query(None, description="Only this indicator, e.g. R01 (or MODEL)."),
):
    if astronaut_id is None and day is None and indicator_id is None:
        return error(400, "give at least one filter: astronaut_id, day or indicator_id")
    where, params = [], []
    if astronaut_id is not None:
        if not known_astronaut(astronaut_id):
            return error(404, f"unknown astronaut '{astronaut_id}'")
        where.append("a.astronaut_id = ?"); params.append(astronaut_id)
    if day is not None:
        if not known_day(day):
            return error(404, f"mission day {day} is not in the mission")
        where.append("t.mission_day = ?"); params.append(day)
    if indicator_id is not None:
        if indicator_id == MODEL:
            where.append("a.indicator_id IS NULL")
        else:
            where.append("a.indicator_id = ?"); params.append(indicator_id)
    return items(rows(f"SELECT {ALERT_COLS} {ALERT_FROM} WHERE {' AND '.join(where)} "
                      "ORDER BY t.mission_day, a.astronaut_id, a.alert_id", params))


@router.post("/alerts/{alert_id}/acknowledge", summary="Mark one alert as seen",
             description="Sets `acknowledged` = 1 on that alert and returns it. The engine keeps this when it "
                         "runs again. HTTP 404 if the alert does not exist.\n\n"
                         "Example: `POST /alerts/412/acknowledge`")
def acknowledge_alert(alert_id: int):
    con = connect()
    try:
        with con:
            changed = con.execute("UPDATE alerts SET acknowledged = 1 WHERE alert_id = ?", (alert_id,)).rowcount
    finally:
        con.close()
    if not changed:
        return error(404, f"alert {alert_id} does not exist")
    return {"ok": True, "alert": rows(f"SELECT {ALERT_COLS} {ALERT_FROM} WHERE a.alert_id = ?", (alert_id,))[0]}


class EpisodeKey(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"astronaut_id": "A2", "indicator_id": "R01",
                                                               "start_day": 60}]})
    astronaut_id: str = Field(description="The episode's astronaut_id, e.g. 'A2', or 'CREW' for a cabin episode.")
    indicator_id: str = Field(description="The episode's indicator_id, e.g. 'R01' (or 'MODEL').")
    start_day: int = Field(description="The episode's start_day.")


@router.post("/episodes/acknowledge", summary="Mark a whole episode as seen",
             description="""
Sets `acknowledged` = 1 on every alert of that astronaut and indicator between the episode's `start_day` and
`end_day`, and on the episode row. For a 'CREW' episode it covers every astronaut's alerts of that indicator
on those days. A new alert day later reopens the episode.

**Reply:** `{"ok": true, "alerts_acknowledged": n}`. HTTP 404 if there is no such episode.
""")
def acknowledge_episode(key: EpisodeKey):
    ep = rows("SELECT start_day, end_day FROM alert_episodes WHERE astronaut_id = ? AND indicator_id = ? "
              "AND start_day = ?", (key.astronaut_id, key.indicator_id, key.start_day))
    if not ep:
        return error(404, f"no episode for {key.astronaut_id} {key.indicator_id} starting on day {key.start_day}")
    where, params = ["t.mission_day BETWEEN ? AND ?"], [ep[0]["start_day"], ep[0]["end_day"]]
    if key.indicator_id == MODEL:
        where.append("a.indicator_id IS NULL")
    else:
        where.append("a.indicator_id = ?"); params.append(key.indicator_id)
    if key.astronaut_id != "CREW":
        where.append("a.astronaut_id = ?"); params.append(key.astronaut_id)
    con = connect()
    try:
        with con:
            n = con.execute(f"UPDATE alerts SET acknowledged = 1 WHERE alert_id IN "
                            f"(SELECT a.alert_id {ALERT_FROM} WHERE {' AND '.join(where)})", params).rowcount
            con.execute("UPDATE alert_episodes SET acknowledged = 1 WHERE astronaut_id = ? AND indicator_id = ? "
                        "AND start_day = ?", (key.astronaut_id, key.indicator_id, key.start_day))
    finally:
        con.close()
    return {"ok": True, "alerts_acknowledged": n}


# ------------------------------------------------------------------ charts
@router.get("/trends", summary="One measure of one astronaut over time",
            description="""
Daily values of one metric from `daily_features`, with the date of each mission day, plus the astronaut's
personal `baseline` for that metric (`median`, `robust_sd`, `computed_from`) or null if it has none.
HTTP 404 if the astronaut is unknown or the metric has no values for that astronaut. `GET /metrics` lists
the metric names.

Example: `GET /trends?astronaut_id=A2&metric=sleep_h_7d_mean&from_day=55&to_day=70`
""")
def trends(
    astronaut_id: str = Query(..., description="e.g. A2"),
    metric: str = Query(..., description="A metric name from GET /metrics, e.g. sleep_h."),
    from_day: int = Query(1, description="First mission day to return."),
    to_day: int = Query(100000, description="Last mission day to return (default: to the end)."),
):
    if not known_astronaut(astronaut_id):
        return error(404, f"unknown astronaut '{astronaut_id}'")
    if not rows("SELECT 1 FROM daily_features WHERE astronaut_id = ? AND metric = ? LIMIT 1", (astronaut_id, metric)):
        return error(404, f"no values of '{metric}' for {astronaut_id}")
    found = rows("SELECT f.mission_day, t.date, f.value FROM daily_features f "
                 "LEFT JOIN mission_timeline t USING (mission_day) "
                 "WHERE f.astronaut_id = ? AND f.metric = ? AND f.mission_day BETWEEN ? AND ? ORDER BY f.mission_day",
                 (astronaut_id, metric, from_day, to_day))
    base = rows("SELECT median, robust_sd, computed_from FROM baselines WHERE astronaut_id = ? AND metric = ?",
                (astronaut_id, metric))
    return items(found, metric=metric, astronaut_id=astronaut_id, baseline=base[0] if base else None)


@router.get("/metrics", summary="The metric names that can be charted",
            description="The distinct metric names in `daily_features`, for `GET /trends`.\n\nExample: `GET /metrics`")
def metrics():
    return items([r["metric"] for r in rows("SELECT DISTINCT metric FROM daily_features ORDER BY metric")])


@router.get("/environment/daily", summary="Daily cabin and radiation values",
            description="""
Rows of `env_daily` that belong to a mission day: `mission_day`, `date`, `metric`, `value`, `unit`, `source`,
`is_real`, `coverage_pct`, `complete`, `value_id`. `complete` = 0 marks a day with too few readings.

Without `metric`, the reply lists which metrics and sources are available instead.

Example: `GET /environment/daily?metric=co2_1h_max_mmhg&from_day=10&to_day=20`
""")
def environment_daily(
    metric: Optional[str] = Query(None, description="e.g. co2_1h_max_mmhg. Leave out to list what is available."),
    from_day: int = Query(1, description="First mission day to return."),
    to_day: int = Query(100000, description="Last mission day to return (default: to the end)."),
):
    if metric is None:
        return items(rows("SELECT metric, source, unit, COUNT(*) AS days, MIN(mission_day) AS first_day, "
                          "MAX(mission_day) AS last_day FROM env_daily WHERE mission_day IS NOT NULL "
                          "GROUP BY metric, source ORDER BY metric, source"))
    if not rows("SELECT 1 FROM env_daily WHERE metric = ? AND mission_day IS NOT NULL LIMIT 1", (metric,)):
        return error(404, f"no daily values of '{metric}' on mission days")
    return items(rows("SELECT mission_day, date, metric, value, unit, source, is_real, coverage_pct, complete, value_id "
                      "FROM env_daily WHERE metric = ? AND mission_day BETWEEN ? AND ? ORDER BY mission_day, source",
                      (metric, from_day, to_day)), metric=metric)


@router.get("/space-weather/events", summary="Solar particle events and their energy channels",
            description="""
Rows of `spe_events`, each with its `channels` (from `spe_channels`) and the `mission_day` of its onset:
the onset date matched to the replayed real date of the mission, else to the mission's own date; null if the
event falls outside the mission.

Example: `GET /space-weather/events`
""")
def space_weather_events():
    ev = rows("SELECT e.*, COALESCE(r.mission_day, d.mission_day) AS mission_day FROM spe_events e "
              "LEFT JOIN mission_timeline r ON r.replay_date = substr(e.onset_time, 1, 10) "
              "LEFT JOIN mission_timeline d ON d.date = substr(e.onset_time, 1, 10) ORDER BY e.onset_time")
    ch = rows("SELECT event_key, channel, min_energy_mev, instrument, time, sep_id FROM spe_channels "
              "ORDER BY min_energy_mev")
    for e in ev:
        e["channels"] = [{k: v for k, v in c.items() if k != "event_key"} for c in ch if c["event_key"] == e["event_key"]]
    return items(ev)


# ------------------------------------------------------------------ where a number comes from
@router.get("/values/{value_id}", summary="Where a number comes from (knowledge base value)",
            description="""
The `kb_values` row for a Value ID: value, unit, value type, source document, PDF page, exact quote and status.
Several IDs can be given, separated by commas. IDs that do not exist are listed in `missing`; HTTP 404 if none
of them exists.

Example: `GET /values/V008,V011`
""")
def values(value_id: str):
    ids = [v.strip() for v in value_id.split(",") if v.strip()]
    found = rows(f"SELECT * FROM kb_values WHERE value_id IN ({','.join('?' * len(ids))}) ORDER BY value_id", ids) if ids else []
    if not found:
        return error(404, f"no knowledge base value {value_id}")
    return items(found, missing=[v for v in ids if v not in {r["value_id"] for r in found}])


@router.get("/rules", summary="The enabled alert rules",
            description="Rows of `rules` that are enabled, each with its `value_id`, for a "
                        "\"why did this alert fire\" panel. An alert's `rule_id` points at one of these.\n\n"
                        "Example: `GET /rules?indicator_id=R01`")
def rules(indicator_id: Optional[str] = Query(None, description="Only this indicator's rules, e.g. R01.")):
    if indicator_id is None:
        return items(rows("SELECT * FROM rules WHERE enabled = 1 ORDER BY rule_id"))
    return items(rows("SELECT * FROM rules WHERE enabled = 1 AND indicator_id = ? ORDER BY rule_id", (indicator_id,)))
