/**
 * MOCK data for the Crew Medical Officer dashboard.
 *
 * Triage, alert severity and the risk scores behind the timeline are produced by the
 * backend Rules Engine / triage layer (engine/rules.py, engine/triage.py). This file only
 * carries the presentation payload; no medical logic is evaluated in the frontend.
 */
import { crew } from "./crew";

export const medicalMission = {
  mission: "Expedition 72",
  missionDay: 66,
  openAlerts: 4,
};

/**
 * Alert queue. `code` links an alert to a crew member; severity/tone come from the engine.
 */
export const alertQueue = [
  { id: "a2-sleep-eva", code: "A2", title: "Sleep before EVA", status: "RED", tone: "red" },
  { id: "a2-workload", code: "A2", title: "Work overload", status: "RED", tone: "red" },
  { id: "a2-pvt", code: "A2", title: "Slow PVT sessions", status: "Yellow", tone: "yellow" },
  { id: "a3-back", code: "A3", title: "Back pain", status: "Yellow", tone: "yellow" },
];

export const criticalTask = {
  code: "A2",
  title: "EVA",
  startTime: "08:00",
  missionDay: 67,
  warning: "A2 is currently RED before a critical task.",
  reviewedMessage: "EVA timing review has been recorded.",
  attentionCode: "red",
};

/**
 * Risk progression for the selected crew member.
 * `coverage` makes the data window and its completeness explicit, so a partial window
 * is never presented as a complete record.
 */
export const riskTimeline = {
  subtitle: "Risk progression · Day 58–67",
  coverage: {
    from: "Day 58",
    to: "Day 67",
    coveredDays: 10,
    expectedDays: 10,
    label: "10/10 days",
    status: "complete",
  },
  events: [
    { id: "d58", day: "58", title: "Work overload", detail: "9.5 h workdays", tone: "yellow" },
    { id: "d60", day: "60", title: "Sleep loss", detail: "7-day mean below 6 h", tone: "red" },
    { id: "d61", day: "61", title: "PVT deterioration", detail: "Above personal baseline + 2 SD", tone: "yellow" },
    { id: "d65", day: "65", title: "Mood decline", detail: "Self-report 3/5", tone: "yellow" },
    { id: "d67", day: "67", title: "Upcoming EVA", detail: "08:00 · Review timing", tone: "red" },
  ],
};

export const medicalCrew = crew;
