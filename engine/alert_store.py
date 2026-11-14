"""
Writes one engine's alerts without losing what people did with them.

rules.py and anomaly.py recompute every alert on each run. Deleting and re-inserting them would reset
`acknowledged` and `synced_to_ground` and change every alert_id. sync_alerts() instead:
  - keeps an alert that is produced again (same astronaut, time, rule): same alert_id, same acknowledged /
    synced_to_ground; only level, reason and value_ids are refreshed
  - inserts alerts that are new
  - deletes alerts that are no longer produced (the data or the rule changed)
"""
import pandas as pd


def sync_alerts(con, source_engine, rows):
    """rows: list of dicts with astronaut_id, time, indicator_id, level, rule_id, reason, value_ids."""
    key = lambda a, t, r: (a, t, -1 if r is None or pd.isna(r) else int(r))
    old = {key(a, t, r): i for i, a, t, r in con.execute(
        "SELECT alert_id, astronaut_id, time, rule_id FROM alerts WHERE source_engine = ?", (source_engine,))}
    new = {key(r["astronaut_id"], r["time"], r.get("rule_id")): r for r in rows}
    with con:
        con.executemany("UPDATE alerts SET level = ?, reason = ?, value_ids = ?, indicator_id = ? WHERE alert_id = ?",
                        [(r["level"], r["reason"], r.get("value_ids"), r.get("indicator_id"), old[k])
                         for k, r in new.items() if k in old])
        con.executemany("INSERT INTO alerts (astronaut_id, time, indicator_id, level, source_engine, rule_id, reason, value_ids) "
                        "VALUES (?,?,?,?,?,?,?,?)",
                        [(r["astronaut_id"], r["time"], r.get("indicator_id"), r["level"], source_engine,
                          r.get("rule_id"), r["reason"], r.get("value_ids")) for k, r in new.items() if k not in old])
        con.executemany("DELETE FROM alerts WHERE alert_id = ?", [(i,) for k, i in old.items() if k not in new])
    return {"kept": sum(k in old for k in new), "new": sum(k not in old for k in new),
            "removed": sum(k not in new for k in old)}
