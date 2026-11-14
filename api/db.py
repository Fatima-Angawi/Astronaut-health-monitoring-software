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


def utc(t):
    """ISO time with a zone -> 'YYYY-MM-DDTHH:MM:SSZ'; None if it has no zone or does not parse."""
    try:
        dt = datetime.fromisoformat(t.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    if dt.tzinfo is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
