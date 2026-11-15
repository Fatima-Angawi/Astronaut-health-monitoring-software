/*
 * api.js: the ONLY file that talks to the backend. Every screen imports from here.
 *
 * Settings (ui/.env):
 *   VITE_API_URL=http://localhost:8000   address of the API (default as shown)
 *   VITE_USE_SAMPLES=1                   read ui/public/samples/<name>.json instead of calling the API
 *
 * Field names are the API's own (snake_case, as in the database tables): nothing is renamed on the way through.
 * Every GET returns the API's JSON body: {ok, count, items, ...}. Failures throw ApiError (see below), so a screen
 * can show `error.message` instead of going blank.
 *
 * Mission day: a day that is left out means "the mission clock's current day" (/status, /episodes, /summary).
 * A screen that shows a chosen day should pass it, and pass the same day as `missionDay` when it sends a check-in
 * or a reaction test, so the engine files the readings under that day.
 */

const env = import.meta.env ?? {};

export const settings = {
  baseUrl: (env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, ""),
  useSamples: env.VITE_USE_SAMPLES === "1",
  samplesPath: `${env.BASE_URL || "/"}samples/`,
};

/** Thrown for every failure. `status` is the HTTP status (0 = the server could not be reached). */
export class ApiError extends Error {
  constructor(message, { status = 0, body = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

// ------------------------------------------------------------------ plumbing
function qs(query) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(query || {})) {
    if (v === undefined || v === null || v === "") continue;
    p.set(k, v === true ? "1" : v === false ? "0" : String(v));
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

function errorText(status, data) {
  if (data && typeof data.error === "string") return data.error;                    // the API's own message
  if (data && Array.isArray(data.detail)) {                                          // request validation (HTTP 422)
    return data.detail.map((d) => `${(d.loc || []).slice(1).join(".") || "request"}: ${d.msg}`).join("; ");
  }
  if (data && typeof data.detail === "string") return data.detail;
  return `The API answered with HTTP ${status}`;
}

async function fromSample(name, method) {
  if (method !== "GET") return { ok: true, sample: true };                            // nothing is sent in sample mode
  let res;
  try {
    res = await fetch(`${settings.samplesPath}${name}.json`);
  } catch {
    throw new ApiError(`Sample file ${name}.json could not be loaded`);
  }
  if (!res.ok) throw new ApiError(`Sample file ${name}.json not found`, { status: res.status });
  return res.json();
}

async function request(path, { method = "GET", query, body, sample } = {}) {
  if (settings.useSamples) return fromSample(sample, method);
  let res;
  try {
    res = await fetch(settings.baseUrl + path + qs(query), {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError("Cannot reach the API");
  }
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* not JSON (for example a proxy error page) */
  }
  if (!res.ok) throw new ApiError(errorText(res.status, data), { status: res.status, body: data });
  if (data && data.ok === false) throw new ApiError(data.error || "The API refused the request", { status: res.status, body: data });
  return data;
}

// ------------------------------------------------------------------ mission and crew
/** {days, first_day, last_day, latest_day_with_data, current_day, clock_running, seconds_per_day, replay_sent_through, engine_*} */
export const getMission = () => request("/mission", { sample: "mission" });

/** Start, pause or move the mission clock: {action: "start"|"pause"|"set_day"|"set_speed", day?, seconds_per_day?}. */
export const setClock = (body) => request("/mission/clock", { method: "POST", body, sample: "mission" });

/** {items: [{astronaut_id, role}]}; A1 is the crew medical officer. */
export const getCrew = () => request("/crew", { sample: "crew" });

// ------------------------------------------------------------------ one day
/** Everyone's level on a mission day: {mission_day, date, cabin: [...episodes], items: [{astronaut_id, level, standing_level, ...}]}. */
export const getStatus = (day) => request("/status", { query: { day }, sample: "status" });

/** One astronaut on one day: {status, cards: {pvt_lapses, sleep_h_7d_mean, mood, next_critical_event}, context: {...}}. */
export const getSummary = (astronautId, day) =>
  request("/summary", { query: { astronaut_id: astronautId, day }, sample: "summary" });

/** Planned EVAs, dockings and the landing, each with days_until. */
export const getEvents = (astronautId, fromDay, toDay) =>
  request("/events", { query: { astronaut_id: astronautId, from_day: fromDay, to_day: toDay }, sample: "events" });

// ------------------------------------------------------------------ alerts
/** Episodes (one problem over several days) with title, first_reason, action and value_ids.
 *  {astronautId, day, minLevel: "yellow"|"orange"|"red", open: true, includeCabin: false} */
export const getEpisodes = ({ astronautId, day, minLevel, open, includeCabin } = {}) =>
  request("/episodes", {
    query: { astronaut_id: astronautId, day, min_level: minLevel, open, include_cabin: includeCabin },
    sample: "episodes",
  });

/** Single alerts; at least one filter is needed. {astronautId, day, indicatorId} */
export const getAlerts = ({ astronautId, day, indicatorId } = {}) =>
  request("/alerts", { query: { astronaut_id: astronautId, day, indicator_id: indicatorId }, sample: "alerts" });

export const acknowledgeAlert = (alertId) =>
  request(`/alerts/${encodeURIComponent(alertId)}/acknowledge`, { method: "POST", sample: "alerts" });

/** Takes an item of getEpisodes: its astronaut_id, indicator_id and start_day identify it. */
export const acknowledgeEpisode = (episode) =>
  request("/episodes/acknowledge", {
    method: "POST",
    body: { astronaut_id: episode.astronaut_id, indicator_id: episode.indicator_id, start_day: episode.start_day },
    sample: "episodes",
  });

// ------------------------------------------------------------------ charts and context
/** {metric, astronaut_id, baseline: {median, robust_sd, computed_from} | null, items: [{mission_day, date, value}]} */
export const getTrend = (astronautId, metric, fromDay, toDay) =>
  request("/trends", { query: { astronaut_id: astronautId, metric, from_day: fromDay, to_day: toDay }, sample: "trend" });

/** The metric names getTrend accepts. */
export const getMetrics = () => request("/metrics", { sample: "metrics" });

/** Daily cabin and radiation values. Without a metric: which metrics and sources exist. */
export const getEnvironmentDaily = (metric, fromDay, toDay) =>
  request("/environment/daily", { query: { metric, from_day: fromDay, to_day: toDay }, sample: "environment-daily" });

/** Solar particle events with their channels and the mission day of their onset. */
export const getSpaceWeather = () => request("/space-weather/events", { sample: "space-weather" });

// ------------------------------------------------------------------ where a number comes from
/** Knowledge base rows (value, unit, type, source_doc, pdf_page, quote, status) for one id or a list: "V008" or ["V008", "V011"]. */
export const getValues = (valueIds) => {
  const ids = (Array.isArray(valueIds) ? valueIds : String(valueIds).split(",")).map((v) => v.trim()).filter(Boolean);
  if (!ids.length) throw new ApiError("No value id given");
  return request(`/values/${ids.map(encodeURIComponent).join(",")}`, { sample: "values" });
};

/** The enabled rules, for a "why did this fire" panel. */
export const getRules = (indicatorId) => request("/rules", { query: { indicator_id: indicatorId }, sample: "rules" });

// ------------------------------------------------------------------ sending data (POST /readings)
// Metric names, units and ranges are those of api/metrics_catalog.py; the API rejects anything else.
const SYMPTOMS = ["nasal_congestion", "back_pain", "space_motion_sickness", "insomnia", "headache"];

function whole(name, v, lo, hi) {
  if (!Number.isInteger(v) || v < lo || v > hi) throw new ApiError(`${name} must be a whole number from ${lo} to ${hi}`);
  return v;
}

function number(name, v, lo, hi) {
  if (typeof v !== "number" || !Number.isFinite(v) || v < lo || v > hi) {
    throw new ApiError(`${name} must be a number from ${lo} to ${hi}`);
  }
  return v;
}

/** Builds the rows of one submission: all share one time (now, UTC with a zone), is_real = 1. */
function rowsFor(astronautId, device, missionDay, entries) {
  const time = new Date().toISOString();
  return entries.map(([metric, value, unit]) => ({
    astronaut_id: astronautId,
    type: metric,
    value,
    unit,
    time,
    device,
    is_real: 1,
    ...(Number.isInteger(missionDay) ? { mission_day: missionDay } : {}),
  }));
}

async function postReadings(rows) {
  if (settings.useSamples) return { ok: true, sample: true, accepted: rows.length, duplicates: 0, rejected: [] };
  const res = await request("/readings", { method: "POST", body: rows });
  if (res.accepted === 0 && res.rejected && res.rejected.length) {
    throw new ApiError(`Not accepted: ${res.rejected.map((r) => r.reason).join("; ")}`, { status: 200, body: res });
  }
  return res;
}

/**
 * Daily check-in. values: {mood 1-5, stress 1-5, kss 1-9, symptoms: ["headache", ...], supportRequested: true|false,
 * missionDay}. Anything left out is not sent. Symptoms: nasal_congestion, back_pain, space_motion_sickness,
 * insomnia, headache. Returns the API's {accepted, duplicates, rejected}.
 */
export async function sendCheckin(astronautId, values = {}) {
  const e = [];
  if (values.mood !== undefined) e.push(["mood", whole("Mood", values.mood, 1, 5), "score_1_5"]);
  if (values.stress !== undefined) e.push(["stress", whole("Stress", values.stress, 1, 5), "score_1_5"]);
  if (values.kss !== undefined) e.push(["kss", whole("Sleepiness (KSS)", values.kss, 1, 9), "score_1_9"]);
  if (values.symptoms !== undefined) {
    const bad = values.symptoms.filter((s) => !SYMPTOMS.includes(s));
    if (bad.length) throw new ApiError(`Unknown symptom: ${bad.join(", ")}`);
    e.push(["symptom_logged", values.symptoms.length ? 1 : 0, "bool"]);
    e.push(["headache", values.symptoms.includes("headache") ? 1 : 0, "bool"]);
    for (const s of values.symptoms) e.push([`symptom_${s}`, 1, "bool"]);
  }
  if (values.supportRequested !== undefined) e.push(["support_requested", values.supportRequested ? 1 : 0, "bool"]);
  if (!e.length) throw new ApiError("The check-in is empty");
  return postReadings(rowsFor(astronautId, "app-checkin", values.missionDay, e));
}

/**
 * Reaction test result. result: {lapses (count), slowest10Ms, meanRtMs, missionDay}. The screen computes these from
 * its trials; this only sends them. Returns the API's {accepted, duplicates, rejected}.
 */
export async function sendPvt(astronautId, result = {}) {
  const e = [
    ["pvt_lapses", whole("Lapses", result.lapses, 0, 500), "count"],
    ["pvt_slowest10_ms", number("Slowest 10 %", result.slowest10Ms, 100, 10000), "ms"],
    ["pvt_mean_rt_ms", number("Mean reaction time", result.meanRtMs, 100, 10000), "ms"],
  ];
  return postReadings(rowsFor(astronautId, "app-pvt", result.missionDay, e));
}
