# Deploying (Linux server with nginx)

The API has no login: anyone who can reach it can send data and acknowledge alerts. Keep it behind nginx on
127.0.0.1 and, for anything beyond a demo, add a password or an IP allow-list in nginx.

Run these from the project folder on the server, in this order.

## 1. Code and Python
```bash
git clone https://github.com/Fatima-Angawi/Astronaut-health-monitoring-software.git
cd Astronaut-health-monitoring-software
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
The raw data is in the repo (`data/raw/`). If the UI is built here: `cd ui && npm install && npm run build && cd ..`
(the API serves `ui/dist` at `/` when it exists).

## 2. Settings
```bash
cp deploy/env.example deploy/env
nano deploy/env          # PUBLIC_ORIGIN=https://your-domain, NASA_API_KEY=...
```

## 3. Build the replay (the API must NOT be running)
```bash
.venv/bin/python run_all.py                    # about 18 minutes: makes data/generated and checks everything
.venv/bin/python inputs/replay.py --prepare    # builds data/replay and resets the database to an empty mission
```

## 4. Services
```bash
sed -i "s|PROJECT_DIR|$(pwd)|g; s|SERVICE_USER|$USER|g" deploy/health-api.service deploy/health-replay.service
sudo cp deploy/health-api.service deploy/health-replay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now health-api health-replay
curl http://127.0.0.1:8000/mission             # "current_day": 0, "clock_running": false
```

## 5. nginx and HTTPS
```bash
sed "s|YOUR_DOMAIN|your-domain.example|g" deploy/nginx.conf | sudo tee /etc/nginx/sites-available/health >/dev/null
sudo ln -s /etc/nginx/sites-available/health /etc/nginx/sites-enabled/health
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.example
```

## 6. Start the mission clock
```bash
curl -X POST http://127.0.0.1:8000/mission/clock -H "Content-Type: application/json" -d '{"action":"set_speed","seconds_per_day":60}'
curl -X POST http://127.0.0.1:8000/mission/clock -H "Content-Type: application/json" -d '{"action":"start"}'
```
Other actions: `{"action":"pause"}`, `{"action":"set_day","day":60}`, `{"action":"set_speed","seconds_per_day":10}`.

## Day to day
- Logs: `journalctl -u health-api -f` and `journalctl -u health-replay -f`
- Restart the mission from day 0: `sudo systemctl stop health-api health-replay`, then
  `.venv/bin/python inputs/replay.py --prepare`, then `sudo systemctl start health-api health-replay` and start the clock.
- Back up `data/health.db` (not in git).
