# a FastAPI POST /readings endpoint takes the shared format (astronaut_id, type, value, unit, time, device).
# send() posts one reading in that format. 
#virtual_watch() sends a heart rate around 58 bpm every 5 seconds, as the stand-in for a real watch.

import random
import time
from datetime import datetime, timezone

import requests

URL = "http://localhost:8000/readings"


def send(astronaut_id, type_, value, unit, device="watch-01", is_real=1):
    """Every device sends this same format; adding a device = writing a new adapter."""
    reading = {
        "astronaut_id": astronaut_id,
        "type": type_,
        "value": value,
        "unit": unit,
        "time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "device": device,
        "is_real": is_real,
    }
    requests.post(URL, json=reading, timeout=5).raise_for_status()
    return reading


def virtual_watch(astronaut_id="A2", interval=5):             # team design: virtual watch stand-in (5 s)
    """Stands in for a real watch: a reading every few seconds. Simulated, so is_real = 0."""
    while True:
        hr = round(random.gauss(58, 3))                          # team design: virtual watch stand-in
        print(send(astronaut_id, "heart_rate", hr, "bpm", is_real=0))
        time.sleep(interval)


if __name__ == "__main__":
    virtual_watch()
