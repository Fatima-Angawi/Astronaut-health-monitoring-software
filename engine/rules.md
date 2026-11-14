# rules.py: operators that need extra information

Most rules in `rules.json` only look at **today's value** (e.g. "sleep < 6 h"). A few operators need more, so the engine has to do more work. `rules.json` is the authority; this file explains it.

## 1. `before_critical`: is there a critical task within `threshold` hours?
Used by the 🔴 level for R01 (sleep) and R01c (PVT).

Example: A2's sleep alert is 🟠 on day 74. Is A2 doing an EVA on day 74 or 75?
- **Yes** → raise to 🔴, because a tired astronaut is about to do something dangerous.
- **No** → stays 🟠.

The data is daily, so the hours are rounded up to whole days: `threshold` 24 = a critical event **today or tomorrow**.

The rule can't answer this from A2's readings. It has to look at **`mission_events`**, the table of planned EVAs, dockings and landings, where `critical = 1` marks the dangerous ones. `features.py` turns that into `days_to_next_critical` (0 = today).

Evidence: the Sleep report stresses limits "during periods of critical operations" (V010), and NASA-STD-3001 says to avoid scheduling critical tasks when crew should be sleeping (p51).

## 2. `persists`: has the 🟡 lasted N days in a row?
Used by R10b (heart rate) and R06 (symptoms).

Example, R10b (heart rate above baseline):

| Day | 70 | 71 | 72 |
|---|---|---|---|
| 🟡? | yes | yes | yes |

Three days in a row → 🟠 (V033). If it were yes, **no**, yes → no 🟠, and the count restarts.

The rule can't tell from today alone. `rules.py` computes it in memory from the day's rule results for the whole mission; nothing is stored between runs.

## 3. `consecutive`: same idea, counting test sessions instead of days
Used by R01c (PVT).

Example: the PVT is 🟡 in two tests **in a row** → 🟠 (V017). A day with no test is skipped and does not break the count: yes, *no test*, yes still counts as two sessions in a row. Any of the indicator's yellow rules counts (lapses or slowest 10 %).

## 4. `baseline+2sd`: above the personal baseline
Used by R01c (PVT) and R10b (heart rate).

The metric is compared with the astronaut's own baseline (mission days 1–14) plus `threshold` × robust SD (threshold = 2). Two details from `features.py` (team design):
- the robust SD has a minimum floor, so a very steady person is not flagged by tiny changes;
- rating scales (mood, stress, KSS) use the baseline **mean** as centre, because the median of whole-number ratings moves in whole steps.

## 5. The 7-day sleep mean
`sleep_h_7d_mean` (R01 yellow) needs at least 5 of the 7 nights; with fewer, there is no value and the rule does not fire.

## Why it matters for the code
The simple operators run first, then `and_yellow`, `consecutive` and `persists`, and `before_critical` last, because each builds on the results before it.
