"""
Exports the knowledge base into the database.

  Excel sheet "Knowledge Base"  -> kb_indicators
  Excel sheet "Values"          -> kb_values
  knowledge_base/rules.json     -> rules   (each rule checked against kb_values)

Re-running replaces the three tables' contents (the Excel file is the source of truth).

Usage (from the project root):
  python knowledge_base/export_kb.py
  python knowledge_base/export_kb.py --xlsx path/to/Astronaut_Health_Knowledge_Base_v8.xlsx
"""
import argparse, json, sqlite3, sys
from pathlib import Path
from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_XLSX = ROOT / "knowledge_base" / "Astronaut_Health_Knowledge_Base_v8.xlsx"
RULES = ROOT / "knowledge_base" / "rules.json"
DB = ROOT / "data" / "health.db"


def rows_as_dicts(ws):
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    for r in it:
        if r and r[0] not in (None, ""):
            yield dict(zip(header, r))


def text(v):
    return None if v in (None, "", "—") else str(v).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=str(DEFAULT_XLSX))
    ap.add_argument("--db", default=str(DB))
    args = ap.parse_args()

    if not Path(args.db).exists():
        sys.exit(f"Database not found: {args.db}. Run: python db/init_db.py")
    wb = load_workbook(args.xlsx, read_only=True, data_only=True)

    # ---- indicators
    indicators = []
    for r in rows_as_dicts(wb["Knowledge Base"]):
        if not text(r.get("Risk")):
            continue                                   # empty placeholder rows (R22+)
        indicators.append((
            text(r["ID"]),
            text(r["Risk"]),
            text(r.get("Indicator")) or "(draft – no indicator yet)",
            text(r.get("Unit")),
            text(r.get("App Priority")),
            1 if text(r.get("Value IDs")) else 0,      # in_mvp = has pipeline values
        ))

    # ---- values
    values = []
    for r in rows_as_dicts(wb["Values"]):
        values.append((
            text(r["Value ID"]), text(r.get("Indicator ID")), text(r.get("Field")),
            text(r.get("Value")), text(r.get("Unit")), text(r.get("Value type")),
            text(r.get("Source document")), text(r.get("File name")),
            text(r.get("PDF page")), text(r.get("Exact quote (verbatim from PDF)")),
            text(r.get("Status")),
        ))
    value_ids = {v[0] for v in values}
    indicator_ids = {i[0] for i in indicators}

    # ---- rules
    spec = json.loads(RULES.read_text(encoding="utf-8"))
    rules, problems = [], []
    for n, r in enumerate(spec["rules"], 1):
        if r["indicator_id"] not in indicator_ids:
            problems.append(f"rule {n}: unknown indicator {r['indicator_id']}")
            continue
        if r.get("value_id") and r["value_id"] not in value_ids:
            problems.append(f"rule {n}: value_id {r['value_id']} not in Values sheet")
            continue
        if r.get("value_id") is None and r.get("enabled", True):
            print(f"  note: rule {n} ({r['indicator_id']} {r['level']}) has no value_id – {r.get('note', 'add source')}")
        rules.append((r["indicator_id"], r["level"], r["metric"], r["op"], r.get("threshold"),
                      r.get("window_days"), r.get("value_id"), 1 if r.get("enabled", True) else 0))
    if problems:
        sys.exit("Fix rules.json first:\n  " + "\n  ".join(problems))

    # ---- write
    with sqlite3.connect(args.db) as con:
        con.execute("PRAGMA foreign_keys = ON")
        con.execute("BEGIN")                            # the pragma below only lasts for one open transaction
        con.execute("PRAGMA defer_foreign_keys = ON")   # check at commit: readings/alerts already point at these tables
        con.execute("DELETE FROM rules")
        con.execute("DELETE FROM kb_values")
        con.execute("DELETE FROM kb_indicators")
        con.executemany("INSERT INTO kb_indicators VALUES (?,?,?,?,?,?)", indicators)
        con.executemany("INSERT INTO kb_values VALUES (?,?,?,?,?,?,?,?,?,?,?)", values)
        con.executemany("""INSERT INTO rules (indicator_id, level, metric, op, threshold, window_days, value_id, enabled)
                           VALUES (?,?,?,?,?,?,?,?)""", rules)

    print(f"kb_indicators: {len(indicators)} ({sum(i[5] for i in indicators)} in MVP)")
    print(f"kb_values:     {len(values)}")
    print(f"rules:         {len(rules)} ({sum(1 for r in rules if r[7])} enabled, "
          f"{sum(1 for r in rules if not r[7])} waiting for a source)")


if __name__ == "__main__":
    main()
