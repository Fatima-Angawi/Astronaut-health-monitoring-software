"""
POST /environment – one door for cabin and area-radiation telemetry, from the vehicle or a replay feed.

Accepts ONE reading or a LIST (batch, up to 5000). Each reading:
  {"time": "2026-11-15T06:30:05Z", "metric": "co2_ppm", "value": 2650, "unit": "ppm",
   "sensor": "CDRA-1", "source": "vehicle", "is_real": 1}
Radiation readings may add "latitude", "longitude", "l_value".

Rules:
  - raw readings only (every 5 s, 1 min, ...): the server computes the daily values itself
    (api/env_summary.py), so a real vehicle and a replay give the same env_daily rows
  - metric, unit and range are checked against api/env_catalog.py
  - time must carry a time zone (Z or +hh:mm); it is stored as UTC
  - duplicates (same time + metric + sensor + source) are skipped, so a feed can resend after an outage
  - one bad reading does not block the batch: the reply lists what was rejected and why
"""
from datetime import datetime, timedelta
from typing import List, Optional, Union

from fastapi import APIRouter, Body
from pydantic import BaseModel, ConfigDict, Field

from api.db import connect, utc
from api.env_catalog import ENV_METRICS, check_env
from api.env_summary import summarize
from api.metrics_catalog import as_markdown

MAX_BATCH = 5000         # team design
NEXT_DAY_FROM_H = 21     # team design: >= 21:00 also refreshes the next wake-up date (covers the 21:30 sleep start and the 1-h CO2 window)
router = APIRouter()


EXAMPLE = {"time": "2026-11-15T06:30:05Z", "metric": "co2_ppm", "value": 2650, "unit": "ppm",
           "sensor": "CDRA-1", "source": "vehicle"}


class EnvReading(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [EXAMPLE]})
    time: str = Field(description="When the sensor measured it. ISO 8601 with a zone, e.g. 2026-11-15T06:30:05Z.")
    metric: str = Field(description="What was measured (see the table above).")
    value: float = Field(description="The raw reading, inside the accepted range for that metric.")
    unit: str = Field(description="Must be exactly the unit listed for that metric.")
    sensor: str = Field(description="The individual sensor, e.g. 'CDRA-1', 'DosTel1'.")
    source: str = Field(description="The feed it comes from, e.g. 'vehicle'. Daily values are computed per source.")
    is_real: int = Field(1, description="1 = real measurement (default), 0 = simulated.")
    mission_day: Optional[int] = Field(None, description="Optional. Replay feeds send it; live data gets it "
                                                         "from the mission calendar.")
    latitude: Optional[float] = Field(None, description="Optional, radiation only: orbit position.")
    longitude: Optional[float] = Field(None, description="Optional, radiation only.")
    l_value: Optional[float] = Field(None, description="Optional, radiation only: McIlwain L value.")


DOC = f"""
Send one reading or a list (up to {MAX_BATCH}). Send **raw** readings (every few seconds or minutes):
the server computes the daily values itself (1-hour CO2 peak, sleep-window means, daily dose).

**Reply:** `accepted`, `duplicates`, `rejected` (a list of `{{"index", "reason"}}`) and `daily_rows_updated`.
A reading is rejected when the time has no zone, the metric is not in the table, the unit differs,
or the value is outside the accepted range. The ranges are physical sanity limits, not alert thresholds.

**Accepted metrics**

{as_markdown(ENV_METRICS)}
"""


@router.post("/environment", summary="Cabin and area-radiation telemetry, raw", description=DOC)
def add_environment(payload: Union[EnvReading, List[EnvReading]] = Body(...)):
    items = payload if isinstance(payload, list) else [payload]
    if len(items) > MAX_BATCH:
        return {"ok": False, "error": f"batch of {len(items)} is over {MAX_BATCH}; split it"}

    accepted, duplicates, rejected, touched = 0, 0, [], {}
    with connect() as con:
        for i, r in enumerate(items):
            t = utc(r.time)
            if t is None:
                rejected.append({"index": i, "reason": f"time '{r.time}' needs a time zone (e.g. Z)"}); continue
            _, err = check_env(r.metric, r.value, r.unit)
            if err:
                rejected.append({"index": i, "reason": err}); continue
            cur = con.execute(
                "INSERT OR IGNORE INTO env_readings VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (t, r.metric, r.value, r.unit, r.sensor, r.source, r.is_real, r.mission_day,
                 r.latitude, r.longitude, r.l_value))
            if not cur.rowcount:
                duplicates += 1; continue
            accepted += 1
            day = t[:10]
            touched.setdefault(r.source, set()).add(day)
            if int(t[11:13]) >= NEXT_DAY_FROM_H:       # evening readings also count for the next wake-up date
                nxt = (datetime.fromisoformat(day) + timedelta(days=1)).strftime("%Y-%m-%d")
                touched[r.source].add(nxt)
        daily_rows = sum(summarize(con, src, days) for src, days in touched.items())
    return {"ok": True, "accepted": accepted, "duplicates": duplicates, "rejected": rejected,
            "daily_rows_updated": daily_rows}
