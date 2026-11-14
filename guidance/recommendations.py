"""
Engine step 5: recommendations. Adds the recommended action to every alert and every episode.

The actions are the "Action per level" and "Countermeasure" columns of the Knowledge Base sheet, one entry per
indicator and level, each with the Value IDs it rests on. Nothing is invented here:
  - where the knowledge base has no sourced action, the text says so and the entry is marked TEAM DESIGN
  - R06 has no per-condition actions (V036 is still "to find"), so it only routes to the right person
  - supplements are never suggested for radiation (V061)
Who receives the alert (astronaut / CMO / flight surgeon) is decided by triage.py (V050), not here.

Writes: alerts.action, and the columns title + action + action_value_ids on alert_episodes (the episode gets the
title and action of its highest level). The title is a short plain-words headline for the UI (TITLES below).
Run after triage.py, which rebuilds alert_episodes.
Usage: python guidance/recommendations.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"

# (indicator, level) -> (action text, Value IDs). Source: Knowledge Base sheet unless marked TEAM DESIGN.
ACTIONS = {
    ("R01", "yellow"):  ("Protect the sleep period; consider a nap, the pre-sleep lighting setting and caffeine timing.", "V011"),
    ("R01", "orange"):  ("Crew medical officer: review the schedule and workload for a change.", "V011"),
    ("R01", "red"):     ("Flight surgeon: review the schedule or sleep medication before the critical task.", "V011,V010"),
    ("R01c", "yellow"): ("Repeat the PVT and apply the sleep actions (protect sleep, nap, lighting, caffeine timing).", "V011,V016"),
    ("R01c", "orange"): ("Take the 10-minute PVT and check in with the crew medical officer.", "V017"),
    ("R01c", "red"):    ("Flight surgeon: review fitness for the critical task.", "V010"),
    ("R01d", "yellow"): ("Feeling alert does not mean performance is fine: your PVT is worse than your normal.", "V019,V021"),
    ("R01f", "yellow"): ("Work time is above the nominal 6.5 h day. Noted.", "V022"),
    ("R01f", "orange"): ("Crew medical officer: suggest a schedule change (above 48 h this week).", "V023"),
    ("R01f", "red"):    ("Flight surgeon: review the schedule (critical overload); allow recovery time.", "V024"),
    ("R01g", "yellow"): ("Adjust the crew-quarters settings: sleep targets are 17–28 °C and 40–60 % humidity.", "V053"),
    ("R02", "yellow"):  ("Cognitive score is off-nominal: consider countermeasures such as adjusting the work-rest schedule.", "V072"),
    ("R02", "orange"):  ("Crew medical officer: review the cognitive result and the work-rest schedule.", "V074"),   # TEAM DESIGN routing
    ("R02e", "yellow"): ("Self-care: team meals, views of Earth, leisure time and exercise are the countermeasures used on ISS.", "V027,V028"),
    ("R02e", "orange"): ("Crew medical officer check-in.", "V027"),
    ("R02e", "red"):    ("Flight surgeon / psychological support (private conference).", "V027,V049"),
    ("R10b", "yellow"): ("Re-measure heart rate at rest.", "V033"),
    ("R10b", "orange"): ("Crew medical officer: assess (BP, ECG and pulse oximetry are available on board).", "V033,V031"),
    ("R10b", "red"):    ("Flight surgeon review.", "V033"),
    ("R06", "yellow"):  ("Symptom logged. No per-condition action is available in the knowledge base yet.", "V037,V036"),
    ("R06", "orange"):  ("Crew medical officer: symptom has persisted. No per-condition action is available yet.", "V037,V036"),
    ("R06", "red"):     ("Flight surgeon review.", "V037"),
    ("R03c", "yellow"): ("Headache on a day with cabin CO2 above 2.5 mmHg: logged for the crew medical officer.", "V047,V045,V052"),
    ("R03c", "orange"): ("Cabin CO2 1-hour average is above the 3 mmHg limit: report to the crew medical officer and ground.", "V068,V066"),
    ("R21", "orange"):  ("On track to pass the 600 mSv career limit: keep dose as low as reasonably achievable; report to flight surgeon and mission planning.", "V039,V054"),
    ("R21", "red"):     ("Career dose is above 600 mSv: flight surgeon and mission planning; post-mission follow-up through LSAH.", "V039,V054,V062"),
    ("R21b", "yellow"): ("Solar particle event in progress: crew informed.", "V043"),
    ("R21b", "orange"): ("Review EVA timing with ground; move to the shielded area or reconfigure shielding.", "V055,V056,V057,V058"),
    ("R21b", "red"):    ("Solar particle event during an EVA: flight surgeon and ground; shelter is the countermeasure.", "V058,V055"),
    # TEAM DESIGN: the knowledge base has no action for bone; ARED exercise is the countermeasure in the Fracture ER (p22)
    ("R18", "yellow"):  ("Bone projection is behind the normal path: review resistance-exercise (ARED) adherence.", "V071"),
    ("R18", "orange"):  ("Projected bone density is below the NASA limit: crew medical officer to review the exercise plan.", "V069,V070"),
    # TEAM DESIGN: the model has no NASA source
    ("MODEL", "yellow"): ("Unusual combination of measures: look at the measures listed in the reason. No source-based action.", None),
}
FALLBACK = ("No action is defined for this indicator and level.", None)

# (indicator, level) -> short headline for the UI. TEAM DESIGN wording: each one only restates, in plain words,
# what the rule of that level checks (rules.json); it adds no claim of its own.
TITLES = {
    ("R01", "yellow"):  "Short on sleep this week",
    ("R01", "orange"):  "Short on sleep and slower reactions",
    ("R01", "red"):     "Short on sleep before a critical task",
    ("R01c", "yellow"): "Slower reactions than your normal",
    ("R01c", "orange"): "Slower reactions two tests in a row",
    ("R01c", "red"):    "Slower reactions before a critical task",
    ("R01d", "yellow"): "Feeling alert, but reactions are slower",
    ("R01f", "yellow"): "Long work day",
    ("R01f", "orange"): "Work week above 48 hours",
    ("R01f", "red"):    "Critical work overload",
    ("R01g", "yellow"): "Sleep area outside its target range on a short night",
    ("R02", "yellow"):  "Low cognitive test score",
    ("R02", "orange"):  "Very low cognitive test score",
    ("R02e", "yellow"): "Mood lower than usual for 3 days",
    ("R02e", "orange"): "Mood lower than usual for a week",
    ("R02e", "red"):    "Support requested",
    ("R10b", "yellow"): "Resting heart rate above your normal",
    ("R10b", "orange"): "Resting heart rate high for 3 days",
    ("R10b", "red"):    "Heart rate above the clinical limit",
    ("R06", "yellow"):  "Symptom logged",
    ("R06", "orange"):  "Symptoms logged 4 days in a row",
    ("R06", "red"):     "Red-flag symptom",
    ("R03c", "yellow"): "Headache on a high-CO2 day",
    ("R03c", "orange"): "Cabin CO2 above the 1-hour limit",
    ("R21", "orange"):  "On track to pass the career radiation limit",
    ("R21", "red"):     "Career radiation limit passed",
    ("R21b", "yellow"): "Solar particle event",
    ("R21b", "orange"): "Solar particle event: review EVA plans and shielding",
    ("R21b", "red"):    "Solar particle event during an EVA",
    ("R18", "yellow"):  "Bone projection behind the normal path",
    ("R18", "orange"):  "Projected bone density below the NASA limit",
    ("MODEL", "yellow"): "Unusual combination of measures",
}


def main():
    con = sqlite3.connect(DB, timeout=30)
    al = pd.read_sql("SELECT alert_id, indicator_id, level FROM alerts", con)
    if al.empty:
        raise SystemExit("alerts is empty: run the engine first")
    al["indicator_id"] = al.indicator_id.fillna("MODEL")
    missing = set()
    def action(ind, level):
        if (ind, level) not in ACTIONS:
            missing.add((ind, level))
        return ACTIONS.get((ind, level), FALLBACK)
    with con:
        con.executemany("UPDATE alerts SET action = ? WHERE alert_id = ?",
                        [(action(i, l)[0], int(a)) for a, i, l in zip(al.alert_id, al.indicator_id, al.level)])
        try:
            ep = pd.read_sql("SELECT * FROM alert_episodes", con)
        except Exception:
            ep = None
        if ep is not None and len(ep):
            con.executemany(
                "UPDATE alert_episodes SET title = ?, action = ?, action_value_ids = ? "
                "WHERE astronaut_id = ? AND indicator_id = ? AND start_day = ?",
                [(TITLES.get((i, l)), *action(i, l), a, i, int(s))
                 for a, i, l, s in zip(ep.astronaut_id, ep.indicator_id, ep.level, ep.start_day)])
    print(f"actions written: {len(al):,} alerts" + (f", {len(ep):,} episodes" if ep is not None else " (no episodes: run triage.py first)"))
    for m in sorted(missing):
        print("no action defined for:", m)
    if ep is not None:
        for m in sorted({(i, l) for i, l in zip(ep.indicator_id, ep.level)} - set(TITLES)):
            print("no title defined for:", m)
    con.close()


if __name__ == "__main__":
    main()