import sqlite3, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "health.db"; SCHEMA = ROOT / "db" / "schema.sql"
DB.parent.mkdir(parents=True, exist_ok=True)
if "--reset" in sys.argv and DB.exists():
    DB.unlink()
con = sqlite3.connect(DB)
try:
    if not con.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
    print(len(con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()), "tables")
    con.close()
except sqlite3.Error as e:
    con.close(); DB.unlink()          # never leave a half-built database behind
    sys.exit(f"schema.sql failed, database removed: {e}")
