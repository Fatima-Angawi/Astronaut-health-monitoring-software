"""
Engine step 4: triage. Combines all alerts (rules + anomaly model) into
  1. one level per astronaut per mission day, with who it goes to      -> table triage_daily
  2. episodes: consecutive days of the same problem merged into one    -> table alert_episodes
and fills alerts.escalated_to.

Escalation (V050, team design based on V028, V048, V049):
  yellow -> astronaut (self-care) | orange -> crew medical officer (CMO) | red -> flight surgeon (queued for the delayed link)

Team design choices in this file:
  - A day's level is the highest level among that person's ACUTE alerts that day, cabin alerts included.
    Standing conditions (career dose R21, bone projection R18) build up slowly and get their own column
    `standing_level`, so one long-running condition does not hide what happens today (a day with only
    standing alerts has level 'none').
  - An episode is acknowledged when all of its alerts are acknowledged; a new alert day reopens it.
  - Model alerts (source_engine = 'anomaly_model') count as yellow and never raise a level on their own:
    the model has no NASA source. triage_daily.model_flag records that the model also flagged the day.
  - Cabin-wide alerts (CABIN_METRICS: same value for the whole crew) become ONE episode for 'CREW',
    not one per astronaut.
  - An episode = the same astronaut and indicator alerting on consecutive days (a gap of up to GAP_DAYS quiet
    days does not split it). Its level is the highest level reached; level_days records when each level started.

Both tables are rebuilt on every run. Never reads anomaly_labels or truth files.
Usage: python engine/triage.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"
RANK = {"yellow": 1, "orange": 2, "red": 3}
LEVEL = {v: k for k, v in RANK.items()}
ESCALATE = {"yellow": "astronaut", "orange": "CMO", "red": "flight_surgeon"}       # V050
CABIN_METRICS = {"co2_1h_max_mmhg", "spe_active", "spe_channel_min_mev"}          # TEAM DESIGN: whole-cabin conditions
GAP_DAYS = 1                                                                      # TEAM DESIGN
STANDING_INDICATORS = {"R21", "R18"}   # TEAM DESIGN: slow, cumulative conditions


def main():
    con = sqlite3.connect(DB, timeout=30)
    al = pd.read_sql("SELECT a.alert_id, a.astronaut_id, a.time, a.indicator_id, a.level, a.source_engine, "
                     "a.reason, a.value_ids, a.acknowledged, r.metric FROM alerts a LEFT JOIN rules r USING (rule_id)", con)
    if al.empty:
        raise SystemExit("alerts is empty: run engine/rules.py (and engine/anomaly.py) first")
    day_of = dict(pd.read_sql("SELECT date, mission_day FROM mission_timeline", con).values)
    al["mission_day"] = al.time.str[:10].map(day_of)
    al = al.dropna(subset=["mission_day"])
    al["mission_day"] = al.mission_day.astype(int)
    al["indicator_id"] = al.indicator_id.fillna("MODEL")
    al["rank"] = al.level.map(RANK)
    al["is_model"] = al.source_engine == "anomaly_model"
    al["cabin"] = al.metric.isin(CABIN_METRICS)
    al["standing"] = al.indicator_id.isin(STANDING_INDICATORS)

    # ---- 1. one level per astronaut per day
    daily = []
    for (a, d), g in al.groupby(["astronaut_id", "mission_day"]):
        acute, standing = g[~g.standing], g[g.standing]
        level = LEVEL[int(acute["rank"].max())] if len(acute) else "none"
        st = LEVEL[int(standing["rank"].max())] if len(standing) else "none"
        top = (acute if len(acute) else standing).sort_values("rank", ascending=False).iloc[0]
        daily.append({"astronaut_id": a, "mission_day": d, "level": level,
                      "escalated_to": ESCALATE.get(level), "standing_level": st,
                      "standing_escalated_to": ESCALATE.get(st),
                      "n_alerts": len(g), "indicators": ",".join(sorted(g.indicator_id.unique())),
                      "top_reason": top.reason, "model_flag": int(g.is_model.any())})
    daily = pd.DataFrame(daily)

    # ---- 2. episodes (cabin alerts once for the crew)
    ep_src = al.copy()
    ep_src.loc[ep_src.cabin, "astronaut_id"] = "CREW"
    ep_src = ep_src.drop_duplicates(["astronaut_id", "mission_day", "indicator_id", "level", "metric"])
    episodes = []
    for (a, ind), g in ep_src.groupby(["astronaut_id", "indicator_id"]):
        by_day = g.groupby("mission_day")
        days = sorted(by_day.groups)
        start = prev = days[0]
        def close(s, e):
            part = g[(g.mission_day >= s) & (g.mission_day <= e)]
            top = part["rank"].max()
            first = part.sort_values(["mission_day", "rank"], ascending=[True, False]).iloc[0]
            starts = part.groupby("level").mission_day.min()
            vids = sorted({v.strip() for x in part.value_ids.dropna() for v in x.split(",")})
            episodes.append({"astronaut_id": a, "indicator_id": ind, "level": LEVEL[int(top)],
                             "escalated_to": ESCALATE[LEVEL[int(top)]], "start_day": int(s), "end_day": int(e),
                             "alert_days": int(part.mission_day.nunique()),
                             "level_days": ", ".join(f"{l} from day {int(starts[l])}" for l in RANK if l in starts),
                             "first_reason": first.reason, "value_ids": ",".join(vids),
                             "is_cabin": int(a == "CREW"), "from_model": int(part.is_model.all()),
                             "is_standing": int(ind in STANDING_INDICATORS),
                             "acknowledged": int(part.acknowledged.fillna(0).astype(bool).all())})
        for d in days[1:]:
            if d - prev > GAP_DAYS + 1:
                close(start, prev); start = d
            prev = d
        close(start, prev)
    episodes = pd.DataFrame(episodes).sort_values(["start_day", "astronaut_id"])

    # ---- write
    with con:
        con.execute("DELETE FROM triage_daily")
        daily.to_sql("triage_daily", con, if_exists="append", index=False)
        con.execute("DELETE FROM alert_episodes")
        episodes.to_sql("alert_episodes", con, if_exists="append", index=False)
        con.executemany("UPDATE alerts SET escalated_to = ? WHERE alert_id = ?",
                        [(ESCALATE[l], int(i)) for i, l in zip(al.alert_id, al.level)])

    print(f"alerts: {len(al):,} -> person-days with a level: {len(daily):,} -> episodes: {len(episodes):,}")
    print("\nperson-days by level:")
    print(daily.groupby(["astronaut_id", "level"]).size().unstack(fill_value=0).reindex(columns=["none"] + list(RANK), fill_value=0).to_string())
    print("\nepisodes by indicator and level:")
    print(episodes.groupby(["indicator_id", "level"]).size().unstack(fill_value=0).reindex(columns=list(RANK), fill_value=0).to_string())
    red = episodes[episodes.level == "red"]
    if len(red):
        print("\nred episodes (flight surgeon):")
        print(red[["astronaut_id", "indicator_id", "start_day", "end_day", "level_days"]].to_string(index=False))
    con.close()


if __name__ == "__main__":
    main()
