import { icons, trendLegend } from "./icons";

/**
 * MOCK scenario data for the Astronaut dashboard (clearly labelled, not real NASA data).
 *
 * IMPORTANT: nothing here is a medical threshold. `severity` values are the output of
 * the backend Rules Engine (engine/rules.py) and are shown verbatim; the frontend never
 * derives alert severity or triage. Units come from the backend metric catalog
 * (api/metrics_catalog.py). Timestamps and mission days are UTC.
 */

export const astronautMission = {
  mission: "Expedition 72",
  status: "On Track",
  missionDay: 43,
  missionLength: 180,
};

export const astronautAlert = {
  severity: "RED",
  tone: "red",
  title: "You're short on sleep before tomorrow's EVA.",
  body: "Your average sleep has been 4.8 hours over the last 7 nights, and your reaction test is slower than usual.",
  recommendationLabel: "Recommended:",
  recommendation: "Ask the flight surgeon to review EVA timing",
  severitySource: "Rules Engine",
};

export const astronautMetrics = [
  {
    id: "pvt",
    icon: icons.timer,
    status: "Slower",
    tone: "red",
    title: "Reaction Test",
    value: "8 lapses",
    detail: "Latest PVT",
  },
  {
    id: "sleep",
    icon: icons.moon,
    status: "Low",
    tone: "red",
    title: "Sleep",
    value: "4.8 h",
    detail: "7-day average",
  },
  {
    id: "eva",
    icon: icons.rocket,
    status: "Critical",
    tone: "red",
    title: "Next EVA",
    value: "08:00",
    detail: "Mission Day 67",
  },
  {
    id: "mood",
    icon: icons.brain,
    status: "Declining",
    tone: "orange",
    title: "Mood",
    value: "3 / 5",
    detail: "Self-reported · score 1–5",
  },
];

export const astronautTrends = [
  {
    id: "sleep",
    title: "Sleep Duration",
    subtitle: "Hours per night · 8.5 h target · 6 h alert",
    note: "Illustrative visualization of the scenario, not raw daily source data.",
    yLabels: ["10 h", "8 h", "6 h", "4 h"],
    xLabels: ["53", "56", "59", "62", "66"],
    chartA: "/assets/4fac5.svg",
    chartB: "/assets/18fe0.svg",
    legend: trendLegend,
  },
  {
    id: "pvt",
    title: "Reaction Test (PVT)",
    subtitle: "Reaction lapses · personal baseline comparison",
    note: "Illustrative trend, not exact daily values.",
    yLabels: ["9", "6", "3", "0"],
    xLabels: ["53", "56", "59", "62", "66"],
    chartA: "/assets/26281.svg",
    chartB: "/assets/daec8.svg",
  },
  {
    id: "mood",
    title: "Mood Tracking",
    subtitle: "Self-reported mood · scale 1–5",
    note: "Illustrative trend, exact intermediate values are not provided.",
    yLabels: ["5 / 5", "4 / 5", "3 / 5", "2 / 5", "1 / 5"],
    xLabels: ["53", "56", "59", "62", "66"],
    chartA: "/assets/82bd2.svg",
    chartB: "/assets/9802b.svg",
  },
];

export const astronautActions = [
  {
    id: "eva",
    title: "Review EVA Timing",
    copy: "Ask the flight surgeon to review tomorrow's EVA schedule.",
    icon: icons.actionWarning,
    tag: "Requires Review",
    tone: "red",
  },
  {
    id: "sleep",
    title: "Protect Sleep Period",
    copy: "Aim for a full 8.5-hour sleep period tonight.",
    icon: icons.moon,
    tag: "Important",
    tone: "orange",
  },
  {
    id: "recovery",
    title: "Recovery Plan",
    copy: "Take a short nap this afternoon and use caffeine early.",
    icon: icons.coffee,
    tag: "Suggested",
    tone: "blue",
  },
];

/**
 * Mission context cards. `source` marks the provenance of each value so real NASA
 * feeds are never confused with simulated crew data.
 */
export const astronautContext = [
  {
    id: "space-weather",
    icon: icons.sun,
    title: "Space Weather",
    value: "No SPE",
    detail: "No active event",
    source: "nasa",
  },
  {
    id: "eva",
    icon: icons.calendar,
    title: "Tomorrow's EVA",
    value: "08:00",
    detail: "Requires Review",
    source: "crew",
    alert: true,
  },
  {
    id: "dose",
    icon: icons.dose,
    title: "ISS Dose Today",
    value: "0.55 mGy",
    detail: "NASA RadLab",
    source: "nasa",
  },
  {
    id: "co2",
    icon: icons.radio,
    title: "Cabin CO₂",
    value: "2,480 ppm",
    detail: "Simulated data",
    source: "simulated",
  },
];
