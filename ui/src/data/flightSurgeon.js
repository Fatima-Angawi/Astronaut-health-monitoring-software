/**
 * MOCK data for the Flight Surgeon dashboard (ground medical operations).
 *
 * Everything the surgeon sees is a summary of a downlinked report. Severity values are
 * produced on the ground by the Rules Engine; the frontend never re-derives them.
 */
import { crew } from "./crew";

export const surgeonMission = {
  mission: "Expedition 72",
  crewCount: 4,
  coverageLabel: "Days 63–66",
};

export const delayedLinkReport = {
  title: "Delayed Link Report",
  status: "Received",
  tone: "yellow",
  mission: "Expedition 72",
  coverage: "Days 63–66",
  priorityCase: { code: "A2", severity: "RED", tone: "red" },
  /**
   * The link was delayed, so the window is reported as provisional rather than complete.
   */
  quality: {
    label: "Delayed downlink",
    detail: "4/4 days received, last sample 6 h old",
    status: "partial",
  },
};

export const criticalMedicalAlert = {
  title: "Critical Medical Alert",
  severity: "RED",
  tone: "red",
  headline: "Sleep Loss Before EVA",
  body: "7-day sleep mean: 4.8 hours. Reaction test: 8 lapses, compared with a usual range of 1–5.",
  followUp: "Upcoming EVA · Day 67 · 08:00",
  severitySource: "Rules Engine",
};

export const crewResponse = {
  title: "Crew Response",
  badge: { label: "Actions Taken", tone: "green" },
  findings: [
    "A1 acknowledged 07:55",
    "Sleep period protected",
    "Nap at 13:10",
    "Retest set for 18:00",
  ],
};

export const systemFindings = {
  title: "System Findings",
  badge: { label: "A2", tone: "red" },
  findings: [
    "Sleep mean 4.8 h",
    "8 PVT lapses",
    "9.5 h workdays",
    "EVA Day 67",
  ],
};

export const surgeonCrew = crew;
