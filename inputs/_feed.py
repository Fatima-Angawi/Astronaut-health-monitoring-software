"""Shared sender for the feeds: POST in batches, retry only when the API is unreachable or busy."""
import time
import requests

RETRIES = 5          # team design
TIMEOUT_S = 300      # team design: a 5000-row batch plus the daily summary


def send(url, rows, batch=5000):
    tot = {}
    for i in range(0, len(rows), batch):
        for attempt in range(RETRIES):
            try:
                res = requests.post(url, json=rows[i:i + batch], timeout=TIMEOUT_S)
            except requests.RequestException as e:
                print(f"   API not reachable ({e.__class__.__name__}); retrying in {2 ** attempt}s")
                time.sleep(2 ** attempt); continue
            if res.status_code >= 500:
                print(f"   API error {res.status_code}; retrying in {2 ** attempt}s")
                time.sleep(2 ** attempt); continue
            if res.status_code >= 400:
                raise SystemExit(f"Request refused ({res.status_code}): {res.text[:500]}")
            r = res.json(); break
        else:
            raise SystemExit("API not reachable; nothing lost: run again, duplicates are skipped.")
        if not r.get("ok", True):
            raise SystemExit(f"API refused the batch: {r.get('error')}")
        for k, v in r.items():
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                tot[k] = tot.get(k, 0) + v
        tot["rejected"] = tot.get("rejected", 0) + len(r.get("rejected", []))
        for rej in r.get("rejected", [])[:3]:
            print(f"   rejected #{i + rej['index']}: {rej['reason']}")
    return tot
