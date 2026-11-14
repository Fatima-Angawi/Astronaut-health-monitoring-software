"""
POST /space-weather – solar particle event (SPE) notices, for R21b.

Accepts DONKI SEP records as NASA's DONKI API returns them (https://api.nasa.gov, DONKI "SEP"):
  {"sepID": "2024-02-09T15:00:00-SEP-001", "eventTime": "2024-02-09T15:00Z",
   "instruments": [{"displayName": "GOES-P: SEISS >10 MeV"}],
   "linkedEvents": [{"activityID": "2024-02-09T13:25:00-CME-001"}], "link": "https://..."}
A mission's own space-weather service would send the same fields (team design: DONKI's format is the contract).

  - Records of one event share event_key = first linked activityID (else sepID), so the >10, >30 and
    >100 MeV records of one storm become one event, and re-sending never duplicates.
  - The channel energy is read from the instrument name (">10 MeV" -> 10).
  - onset_time = earliest record; max_channel = highest energy seen so far.
"""
import re
from typing import List, Optional, Union

from fastapi import APIRouter, Body
from pydantic import BaseModel, ConfigDict, Field

from api.db import connect, utc

router = APIRouter()
ENERGY = re.compile(r">=?\s*(\d+(?:\.\d+)?)\s*MeV", re.I)   # ">10 MeV" and ">=10 MeV"
ALLOWED_INSTRUMENTS = ("GOES",)   # team design, as in inputs/donki.md: measured GOES channels only, no models


EXAMPLE = {"sepID": "2024-02-12T08:05:00-SEP-001", "eventTime": "2024-02-12T08:05Z",
           "instruments": [{"displayName": "GOES-P: SEISS >10 MeV"}],
           "linkedEvents": [{"activityID": "2024-02-12T06:36:00-CME-001"}],
           "link": "https://ccmc.gsfc.nasa.gov/DONKI/view/SEP/29156/-1"}


class SepRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", json_schema_extra={"examples": [EXAMPLE]})
    sepID: str = Field(description="DONKI record id.")
    eventTime: str = Field(description="When the channel threshold was crossed. ISO 8601 with a zone.")
    instruments: List[dict] = Field([], description="Each item has a displayName such as "
                                                    "'GOES-P: SEISS >10 MeV'. Only GOES '>N MeV' channels are used.")
    linkedEvents: Optional[List[dict]] = Field(None, description="Optional. The first activityID groups the "
                                                                 "records of one storm into one event.")
    link: Optional[str] = Field(None, description="Optional. Link to the DONKI page.")


DOC = """
Send DONKI SEP records exactly as NASA's DONKI API returns them: one record or a list. Extra fields are ignored.

**Reply:** `new_events`, `new_channels`, and `rejected` (a list of `{"index", "reason"}`).
A record is rejected when `eventTime` has no zone, when no instrument is a GOES channel (forecast models are
excluded), or when no GOES instrument name contains a `>N MeV` energy. Re-sending the same records adds nothing.
"""


@router.post("/space-weather", summary="Solar particle event notices (DONKI SEP format)", description=DOC)
def add_space_weather(payload: Union[SepRecord, List[SepRecord]] = Body(...)):
    items = payload if isinstance(payload, list) else [payload]
    new_events, new_channels, rejected = 0, 0, []
    with connect() as con:
        for i, r in enumerate(items):
            t = utc(r.eventTime)
            if t is None:
                rejected.append({"index": i, "reason": "eventTime needs a time zone"}); continue
            linked = [e.get("activityID") for e in (r.linkedEvents or []) if e.get("activityID")]
            key = linked[0] if linked else r.sepID
            names = [n for n in (ins.get("displayName", "") for ins in r.instruments)
                     if n.startswith(ALLOWED_INSTRUMENTS)]
            if not names:
                rejected.append({"index": i, "reason": "no GOES channel (models are excluded)"}); continue
            found = [(n, float(m.group(1))) for n in names if (m := ENERGY.search(n))]
            if not found:
                rejected.append({"index": i, "reason": f"no '>N MeV' channel in instruments {names}"}); continue
            cur = con.execute("INSERT OR IGNORE INTO spe_events (event_key, onset_time, source_link) VALUES (?,?,?)",
                              (key, t, r.link))
            new_events += cur.rowcount
            con.execute("UPDATE spe_events SET onset_time = MIN(onset_time, ?) WHERE event_key = ?", (t, key))
            for name, mev in found:
                cur = con.execute("INSERT OR IGNORE INTO spe_channels VALUES (?,?,?,?,?,?)",
                                  (key, f">{mev:g} MeV", mev, name, t, r.sepID))
                new_channels += cur.rowcount
            top = con.execute("SELECT MAX(min_energy_mev) FROM spe_channels WHERE event_key = ?", (key,)).fetchone()[0]
            con.execute("UPDATE spe_events SET max_channel = ? WHERE event_key = ?", (f">{top:g} MeV", key))
    return {"ok": True, "new_events": new_events, "new_channels": new_channels, "rejected": rejected}
