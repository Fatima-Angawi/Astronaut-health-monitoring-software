"""
DONKI feed: sends SPE records to POST /space-weather.

Reads the JSON that donki.py saved (a list of DONKI SEP records, or a dict holding that list)
and posts the records unchanged; the server groups them into events.

Usage (API running):  python inputs/send_donki.py data/raw/donki/SPE_events.json
"""
import argparse
import json

from _feed import send


def records(obj):
    if isinstance(obj, list):
        return [r for r in obj if isinstance(r, dict) and "sepID" in r]
    if isinstance(obj, dict):
        for v in obj.values():
            found = records(v)
            if found:
                return found
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", nargs="?", default="data/raw/donki/SPE_events.json")
    ap.add_argument("--url", default="http://localhost:8000/space-weather")
    a = ap.parse_args()
    recs = records(json.load(open(a.file, encoding="utf-8")))
    if not recs:
        raise SystemExit(f"No DONKI SEP records (with 'sepID') found in {a.file}")
    print(f"{len(recs)} records sent:", send(a.url, recs, batch=500))


if __name__ == "__main__":
    main()
