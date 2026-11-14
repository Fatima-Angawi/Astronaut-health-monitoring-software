from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import readings, environment, space_weather, views

DESCRIPTION = """
The contract for anything that sends data to the crew health monitor. Three doors, one per data type:

| Send | To | Format |
|---|---|---|
| A crew measurement (watch, check-in, dosimeter, virtual device) | `POST /readings` | one reading or a list |
| Cabin or area-radiation telemetry, raw | `POST /environment` | one reading or a list |
| A solar particle event notice | `POST /space-weather` | DONKI SEP records, unchanged |

Rules that apply to every door:

- **Times are UTC with a zone**, e.g. `2026-11-15T06:30:05Z`. A time with no zone is rejected.
- **Send one object or a list** (up to 5000 per request).
- **Re-sending is safe**: a reading already stored is counted under `duplicates`, never stored twice.
- **One bad reading does not block the rest**: the reply lists each rejected item with its position and reason.
- Simulated data uses the same doors with `is_real: 0`.

The **UI views** section holds the read endpoints for a frontend (status, episodes, alerts, trends, sources).
They only read what the engine has computed; the two `acknowledge` endpoints are the only ones that change anything.

Open an endpoint below and press **Try it out** to send a test request.
"""

app = FastAPI(title="Crew Health Monitor", description=DESCRIPTION, version="0.1")
app.add_middleware(CORSMiddleware,          # a frontend on this machine (any port) may call the API
                   allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(readings.router)        # crew:(devices, app, virtual device)
app.include_router(environment.router)     # cabin + area radiation telemetry
app.include_router(space_weather.router)   # SPE notices (DONKI format)
app.include_router(views.router)           # read endpoints for the UI (+ acknowledge)