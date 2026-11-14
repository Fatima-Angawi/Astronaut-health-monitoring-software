# donki.py: design notes

DONKI creates a separate record for each instrument that saw the same event. Three things to handle when building the code.

## 1. Combine records into one event
Records for the same event share the same `linkedEvents` (the same CME or flare). For example, all 8 records on 9 Feb point to `2024-02-09T13:23:00-CME-001`.
Group by `linkedEvents` so the astronaut gets **one alert per event**, not 8.

## 2. Real measurements vs. models
- `MODEL: REleASE:...` is a forecast model, **not** a measurement. Exclude it.
- GOES, SOHO and STEREO-A are instruments that actually measured the particles.
- **Use GOES as the alert source** (team design decision). GOES satellites orbit Earth, so they are closest to what the space station experiences. STEREO-A sits elsewhere in the solar system.

## 3. Energy level = severity
The `displayName` field contains the energy (`>10 MeV`, `15.8–39.8 MeV`, `>100 MeV`). This follows the radiation report (p12):

> "Proton energies above 30 megaelectron volt (MeV) (fluence >30MeV) require shielding"

The alert levels are set in `rules.json` (the authority); they are a team design choice:

| Event | Level |
|---|---|
| Any active SPE | 🟡 inform the crew |
| Highest channel >= 30 MeV, or any SPE with an EVA planned in the next 3 days | 🟠 review EVA plans + shielding |
| Any SPE on a day with an EVA | 🔴 |

The EVA-based levels follow V058 (greatest concern during EVA).

## Demo scenario
The **12 Feb 10:15** GOES event (>100 MeV) is the strongest in the file. Put a planned EVA on that date in `simulator.py`, show the system raising the alert, and recommend moving to a shielded area (V055–V057).
