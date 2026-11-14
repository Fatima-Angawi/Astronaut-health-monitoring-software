from typing import List, Optional, Union

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field, ConfigDict

from api.db import connect, utc
from api.metrics_catalog import METRICS, as_markdown, check

MAX_BATCH = 5000                                # team design: keeps one request under a few MB
router = APIRouter()

EXAMPLE = {"astronaut_id": "A2", "type": "heart_rate", "value": 58, "unit": "bpm",
           "time": "2026-11-15T06:30:05Z", "device": "watch-01"}


class Reading(BaseModel):
    model_config = ConfigDict(populate_by_name=True, json_schema_extra={"examples": [EXAMPLE]})
    astronaut_id: str = Field(description="Crew member, e.g. 'A1'. Must exist in the crew table.")
    metric: str = Field(alias="type", description="What was measured (see the table above). "
                                                  "The field may be named 'type' or 'metric'.")
    value: float = Field(description="The measurement, inside the accepted range for that metric.")
    unit: str = Field(description="Must be exactly the unit listed for that metric.")
    time: str = Field(description="When the device measured it (not arrival time). ISO 8601 with a zone, "
                                  "e.g. 2026-11-15T06:30:05Z.")
    device: str = Field(description="Who is sending, e.g. 'watch-01', 'app', 'simulator'. Stored as the source.")
    is_real: int = Field(1, description="1 = real measurement (default), 0 = simulated.")
    mission_day: Optional[int] = Field(None, description="Optional. Negative = preflight "
                                                         "(e.g. baseline cognition tests).")
    availability: str = Field("live", description="'live' (default) or 'after_return' (e.g. post-flight DXA).")


DOC = f"""
Send one reading or a list (up to {MAX_BATCH}).

**Reply:** `accepted`, `duplicates`, and `rejected` (a list of `{{"index", "reason"}}`).
A reading is rejected when the astronaut is unknown, the time has no zone, the metric is not in the table,
the unit differs, or the value is outside the accepted range. The ranges are physical sanity limits, not alert thresholds.

**Accepted metrics**

{as_markdown(METRICS)}
"""


@router.post("/readings", summary="Crew measurements, per astronaut", description=DOC)
def add_readings(payload: Union[Reading, List[Reading]] = Body(...)):
    items = payload if isinstance(payload, list) else [payload]
    if len(items) > MAX_BATCH:
        return {"ok": False, "error": f"batch of {len(items)} is over {MAX_BATCH}; split it"}

    accepted, duplicates, rejected = 0, 0, []
    with connect() as con:
        crew = {r[0] for r in con.execute("SELECT astronaut_id FROM crew")}
        if not crew:
            return {"ok": False, "error": "crew table is empty: run inputs/load_db.py first"}
        for i, r in enumerate(items):
            if r.astronaut_id not in crew:
                rejected.append({"index": i, "reason": f"unknown astronaut '{r.astronaut_id}'"}); continue
            t = utc(r.time)
            if t is None:
                rejected.append({"index": i, "reason": f"time '{r.time}' needs a time zone (e.g. Z)"}); continue
            ind, err = check(r.metric, r.value, r.unit)
            if err:
                rejected.append({"index": i, "reason": err}); continue
            cur = con.execute(
                """INSERT OR IGNORE INTO readings
                   (astronaut_id, time, mission_day, indicator_id, metric, value, unit, source, is_real, availability)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (r.astronaut_id, t, r.mission_day, ind, r.metric, r.value, r.unit,
                 r.device, r.is_real, r.availability))
            if cur.rowcount:
                accepted += 1
            else:
                duplicates += 1
    return {"ok": True, "accepted": accepted, "duplicates": duplicates, "rejected": rejected}
