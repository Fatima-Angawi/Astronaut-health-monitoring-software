# ORVITALIS — Astronaut Health Monitoring

**Live demo:** [https://orvitalis.us](https://orvitalis.us) — the mission replay is parked at day 66; open the astronaut view and click **Why?** on the red alert to see the NASA source and page behind it.

NASA Space Apps Challenge 2026 · Challenge 05 · Team ORVITALIS, Jeddah, Saudi Arabia

## What it does
ORVITALIS turns daily crew and mission data into one alert level per astronaut per day and sends it to the person who must act:
yellow → astronaut, orange → crew medical officer, red → flight surgeon.
Every alert shows its reason, the action to take, and the NASA document and page behind its threshold.

## How it works
1. **Knowledge base** – 76 values extracted from 6 HRP Evidence Reports and NASA-STD-3001 Vol 1 & 2, each with document, page and quote (49 verified, 21 team design, 6 still open).
2. **Inputs** – API endpoints for crew readings, cabin/radiation telemetry and space weather.
3. **Engine** – daily features (7-day means, personal baselines) → 34 enabled rules citing a Value ID → Isolation Forest for unusual combinations → triage.
4. **UI** – React app with a "Why?" panel showing the source.

A live replay sends one mission day per minute; the engine reruns as each day arrives.

## Data
- **Real NASA data (replayed):** DONKI solar particle events, RadLab ISS radiation dose (DOSTEL, ALTEA), OSDR RR-1 cabin CO₂.
- **Simulated crew data:** we ran 33 queries on NASA OSDR (355 studies); no open dataset had human sleep, reaction time (PVT), mood, heart rate, blood pressure or SpO₂. Crew indicators are generated from HRP Evidence Report values.

## Built with
Python, FastAPI, SQLite, pandas, NumPy, scikit-learn, React, Vite · hosted on Azure with nginx and HTTPS.
Claude (Anthropic) was used as an AI assistant for code and documentation; all output was reviewed and tested by the team.

## Run it locally
```bash
git clone https://github.com/Fatima-Angawi/Astronaut-health-monitoring-software.git
cd Astronaut-health-monitoring-software
pip install -r requirements.txt
cp deploy/env.example deploy/env   # add your NASA_API_KEY
python run_all.py                  # seed data, run engine, run tests
uvicorn api.main:app --reload      # API on http://127.0.0.1:8000
cd ui && npm install && npm run dev
```

## Team
Fatima Angawi · Ahmed Kamel · Layan Alqurashi · Talal Alomayri · Afnan Alsharif
