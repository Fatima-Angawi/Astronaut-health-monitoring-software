"""
Shared database connection and time check for every route.
- timeout and WAL mode: a reader no longer makes a write fail with "database is locked".
- utc(): every time must carry a zone (design rule 3); stored as YYYY-MM-DDTHH:MM:SSZ.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "health.db"
BUSY_TIMEOUT_S = 30                    # team design


def connect():
    con = sqlite3.connect(DB, timeout=BUSY_TIMEOUT_S)
    con.execute("PRAGMA journal_mode=WAL")
    return con


STATE_DDL = "CREATE TABLE IF NOT EXISTS system_state (key TEXT PRIMARY KEY, value TEXT)"


def state_get(con, key, default=None):
    """One value from system_state (always text), or `default`."""
    con.execute(STATE_DDL)
    r = con.execute("SELECT value FROM system_state WHERE key = ?", (key,)).fetchone()
    return default if r is None or r[0] is None else r[0]


def state_set(con, **values):
    """Write one or more system_state keys (committed by the caller's `with con:`)."""
    con.execute(STATE_DDL)
    con.executemany("INSERT INTO system_state (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    [(k, str(v)) for k, v in values.items()])


def utc(t):
    """ISO time with a zone -> 'YYYY-MM-DDTHH:MM:SSZ'; None if it has no zone or does not parse."""
    try:
        dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
