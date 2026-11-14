# rules.py: operators that need extra information

Most rules in `rules.json` only look at **today's value** (e.g. "sleep < 6 h"). Three operators need more, so the engine has to do more work.

## 1. `before_critical`: is there a critical task in the next 24 hours?
Used by the 🔴 level for R01 (sleep) and R01c (PVT).

Example: A2's sleep alert is 🟠 on day 74. Is A2 doing an EVA on day 75?
- **Yes** → raise to 🔴, because a tired astronaut is about to do something dangerous.
- **No** → stays 🟠.

The rule can't answer this from A2's readings. It has to look at **`mission_events`**, the table of planned EVAs, dockings and landings, where `critical = 1` marks the dangerous ones. So the simulator must create the mission events first.

Evidence: the Sleep report stresses limits "during periods of critical operations" (V010), and NASA-STD-3001 says to avoid scheduling critical tasks when crew should be sleeping (p51).

## 2. `persists`: has the 🟡 lasted N days in a row?
Used by R10b (heart rate) and R06 (symptoms).

Example, R10b (heart rate above baseline):

| Day | 70 | 71 | 72 |
|---|---|---|---|
| 🟡? | yes | yes | yes |

Three days in a row → 🟠 (V033). If it were yes, **no**, yes → no 🟠, and the count restarts.

The rule can't tell from today alone. The engine has to store each day's rule results (in `alerts`, or a small results table) and look back.

## 3. `consecutive`: same idea, counting sessions instead of days
Used by R01c (PVT).

Example: the PVT is 🟡 in two tests **in a row** → 🟠 (V017). If the astronaut skips a day, the count goes test 1 → test 2, not calendar days.

## Why it matters for the code
For `persists` and `consecutive`, `rules.py` must run **day by day, in order**, and remember yesterday's results. You can't evaluate day 72 without knowing what happened on days 70 and 71.
