#donki.py does the fetching at sync time and saves the events to a local file,
#for example data/spe_events.json. The rest of the system reads from that file instead of calling the API directly

#In our app: donki.py runs every few minutes (live mode) 
#and updates the local file as soon as there’s a connection.

#A real spacecraft gets information from mission control over its communication link, not by APIs.
#So in our design, donki.py stands in for the ground team, 
#and the file it saves represents the alert that would arrive over the link.

import json
import os
import re
import time
from datetime import date, timedelta
from pathlib import Path

import requests

URL = "https://api.nasa.gov/DONKI/SEP"
WINDOW_DAYS = 30                                   # team design: DONKI refuses ranges over 60 days; 30 is its own default
REPLAY_START, DAYS = "2024-01-01", 180             # team design: same replay as simulator.py / send_radlab.py
OUT_FILE = Path(__file__).resolve().parent.parent / "data" / "spe_events.json"
RAW_FILE = Path(__file__).resolve().parent.parent / "data" / "raw" / "donki" / "SPE_events.json"   # read by send_donki.py


def _channel(display_name):
    # "GOES-P: SEISS >100 MeV" -> (">100 MeV", 100.0); only the part before "MeV" is read,
    # so digits in satellite names (GOES-16) are ignored
    m = re.search(r"(>?\s*(\d+(?:\.\d+)?)(?:-\d+(?:\.\d+)?)?)\s*MeV", display_name)
    return (m.group(1).replace(" ", "") + " MeV", float(m.group(2))) if m else None


def _fetch_window(start, end, retries=3):
    params = {"startDate": start, "endDate": end, "api_key": os.environ["NASA_API_KEY"]}
    for attempt in range(retries):
        r = requests.get(URL, params=params, timeout=30)
        if r.status_code in (429, 503):
            time.sleep(2 ** attempt)
            continue
        if not r.ok:                               # no raise_for_status(): its message prints the URL with the key
            raise SystemExit(f"DONKI refused {start}..{end} ({r.status_code}): {r.text[:200]}")
        return r.json() if r.text.strip() else []  # empty body = no events
    raise SystemExit(f"DONKI busy for {start}..{end} after {retries} tries; run again later")


def _fetch(start, end):
    """All SEP records from start to end (YYYY-MM-DD, inclusive), fetched in windows DONKI accepts."""
    day, last, seen, out = date.fromisoformat(start), date.fromisoformat(end), set(), []
    while day <= last:
        stop = min(day + timedelta(days=WINDOW_DAYS - 1), last)
        for rec in _fetch_window(day.isoformat(), stop.isoformat()):
            if rec["sepID"] not in seen:
                seen.add(rec["sepID"]); out.append(rec)
        day = stop + timedelta(days=1)
    return out


def get_events(start, end, records=None):
    """One entry per event (grouped by linkedEvents), GOES measurements only."""
    events = {}
    for rec in (records if records is not None else _fetch(start, end)) or []:
        linked = rec.get("linkedEvents") or []
        key = linked[0]["activityID"] if linked else rec["sepID"]
        for inst in rec.get("instruments") or []:
            name = inst["displayName"]
            channel = _channel(name)
            if not name.startswith("GOES") or channel is None:  # GOES-P, GOES-16, ...
                continue
            label, min_mev = channel
            ev = events.setdefault(key, {
                "onset_time": rec["eventTime"],
                "peak_channel_time": rec["eventTime"],
                "energy_channel": label,
                "min_energy_mev": min_mev,
                "instrument": name.split(":")[0],
                "source_link": rec.get("link"),
                "value_id": "V063",
            })
            ev["onset_time"] = min(ev["onset_time"], rec["eventTime"])
            if min_mev > ev["min_energy_mev"]:  # highest channel reached so far
                ev.update(peak_channel_time=rec["eventTime"], energy_channel=label,
                          min_energy_mev=min_mev, instrument=name.split(":")[0],
                          source_link=rec.get("link"))
    return sorted(events.values(), key=lambda e: e["onset_time"])


def sync(start, end):
    """Fetch events; save the raw DONKI SEP list (as the API returned it) to data/raw/donki/SPE_events.json
    for send_donki.py, and the grouped events to data/spe_events.json."""
    raw = _fetch(start, end) or []
    RAW_FILE.parent.mkdir(parents=True, exist_ok=True)
    RAW_FILE.write_text(json.dumps(raw, indent=2), encoding="utf-8")
    events = get_events(start, end, raw)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")
    return events


if __name__ == "__main__":
    # Usage (NASA_API_KEY set):  python inputs/donki.py [--start YYYY-MM-DD] [--end YYYY-MM-DD]
    import argparse
    replay_end = (date.fromisoformat(REPLAY_START) + timedelta(days=DAYS - 1)).isoformat()
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default=REPLAY_START)
    ap.add_argument("--end", default=replay_end)
    a = ap.parse_args()
    if not os.environ.get("NASA_API_KEY"):
        raise SystemExit("Set NASA_API_KEY first (free key from https://api.nasa.gov).")
    found = sync(a.start, a.end)
    n_raw = len(json.loads(RAW_FILE.read_text(encoding="utf-8")))
    print(f"{a.start}..{a.end}: {n_raw} raw SEP records -> {RAW_FILE}")
    print(f"{len(found)} GOES events -> {OUT_FILE}")
    for e in found:
        print(f"  {e['onset_time']}  {e['energy_channel']}")
