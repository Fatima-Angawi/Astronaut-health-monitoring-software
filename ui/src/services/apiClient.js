import axios from "axios";

/**
 * Single HTTP client for the Crew Health Monitor backend (api/main.py).
 *
 * Configure the origin with VITE_API_BASE_URL; the FastAPI dev server default is 127.0.0.1:8000.
 */
const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

/**
 * Endpoints that EXIST today (verified in the backend source).
 *
 * The backend is currently ingestion-only: every door is a POST that writes readings into
 * the database. There is no read API yet, which is why the dashboards render clearly
 * labelled mock data from src/data/*.
 *
 * | Method | Path             | Purpose                                              | Source                        |
 * |--------|------------------|------------------------------------------------------|-------------------------------|
 * | POST   | /readings        | Crew measurements (watch, check-in, dosimeter, ...)   | api/routes/readings.py        |
 * | POST   | /environment     | Cabin + area-radiation telemetry, raw                 | api/routes/environment.py     |
 * | POST   | /space-weather   | Solar particle event notices (DONKI SEP format)       | api/routes/space_weather.py   |
 */
export const INGEST_ENDPOINTS = {
  readings: "/readings",
  environment: "/environment",
  spaceWeather: "/space-weather",
};

/**
 * Read endpoints the dashboards NEED but which DO NOT EXIST YET – to be confirmed with the
 * backend team before the mock data in src/data/* is replaced. Do not assume their shape.
 *
 * | Planned path                     | Needed by              | Payload the UI expects                                  |
 * |----------------------------------|------------------------|---------------------------------------------------------|
 * | GET /crew                        | Medical, Flight Surgeon | Crew roster: id, name, role, severity, last update     |
 * | GET /crew/{id}/readings          | all three              | Time series per metric with unit + mission_day          |
 * | GET /crew/{id}/alerts            | all three              | Open alerts with severity from the Rules Engine         |
 * | GET /crew/{id}/timeline          | Medical                | Risk progression events with day + reason               |
 * | GET /alerts?status=open          | Medical                | Alert queue across the crew                             |
 * | GET /env/summary?source=&days=   | Flight Surgeon         | Environmental daily summary incl. coverage/completeness |
 * | GET /reports/latest              | Flight Surgeon         | Latest downlinked report + coverage window              |
 */
export const PENDING_READ_ENDPOINTS = [
  "/crew",
  "/crew/{id}/readings",
  "/crew/{id}/alerts",
  "/crew/{id}/timeline",
  "/alerts?status=open",
  "/env/summary?source=&days=",
  "/reports/latest",
];

export default apiClient;
