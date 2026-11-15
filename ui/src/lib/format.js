/** Severity words come from the API ("none" | "yellow" | "orange" | "red"); only the colour is chosen here. */
export const LEVEL_TONE = { none: "green", yellow: "yellow", orange: "orange", red: "red" };
export const LEVEL_LABEL = { none: "Normal", yellow: "Yellow", orange: "Orange", red: "Red" };
export const LEVEL_RANK = { none: 0, yellow: 1, orange: 2, red: 3 };

export const tone = (level) => LEVEL_TONE[level] ?? "neutral";
export const label = (level) => LEVEL_LABEL[level] ?? String(level ?? "-");

/**
 * Icon tint per severity (see Icon in components/common). The severity itself is never
 * decided here: it is the level the Rules Engine returned, only its colour is chosen.
 */
export const LEVEL_ICON_TONE = { none: "success", yellow: "warning", orange: "critical", red: "critical" };
export const iconTone = (level) => LEVEL_ICON_TONE[level] ?? "muted";

export const fixed = (v, digits = 1) => (typeof v === "number" ? v.toFixed(digits) : "-");

/** "2027-01-20T08:00Z" -> "08:00" (UTC) */
export const clock = (iso) => (iso ? iso.slice(11, 16) : "-");

export const ROLE_LABEL = { CMO: "Crew Medical Officer", crew: "Crew member" };
export const roleLabel = (role) => ROLE_LABEL[role] ?? role ?? "";

export const splitIds = (...lists) =>
  [...new Set(lists.flatMap((s) => (s ? String(s).split(",") : [])).map((s) => s.trim()).filter(Boolean))];

/** Last mission day whose data has arrived: the replay's progress while one runs, else the latest day on record. */
export const dataThrough = (mission) =>
  mission?.replay_sent_through > 0 ? mission.replay_sent_through : mission?.latest_day_with_data;
