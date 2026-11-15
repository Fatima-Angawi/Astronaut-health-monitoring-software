/**
 * Single source of truth for icon URLs.
 *
 * The Figma export references icons as absolute "/img/<hash>.svg" URLs, so the
 * files live in `public/img` (Vite serves `public/` at the site root).
 */
const BASE = "/img";

export const icons = {
  logo: `${BASE}/aa2ec.svg`,
  status: `${BASE}/2356b.svg`,
  bell: `${BASE}/db6a0.svg`,
  user: `${BASE}/a2a78.svg`,
  warning: `${BASE}/b7e21.svg`,

  // Section navigation
  dashboardNav: `${BASE}/e1e31.svg`,
  sleepNav: `${BASE}/8a9d4.svg`,
  activityNav: `${BASE}/a1e57.svg`,
  heartNav: `${BASE}/e10b7.svg`,
  settingsNav: `${BASE}/d6efe.svg`,

  // Dashboard role icons
  astronautNav: `${BASE}/Astronaut.svg`,
  medicalNav: `${BASE}/medical-stethoscope.svg`,
  surgeonNav: `${BASE}/doctor-profile.svg`,

  // Metric icons
  timer: `${BASE}/c1438.svg`,
  testTimer: `${BASE}/5c239.svg`,
  moon: `${BASE}/81af4.svg`,
  rocket: `${BASE}/c0623.svg`,
  brain: `${BASE}/14773.svg`,
  actionWarning: `${BASE}/bf1b3.svg`,
  coffee: `${BASE}/d81af.svg`,
  sun: `${BASE}/cb309.svg`,
  calendar: `${BASE}/15766.svg`,
  dose: `${BASE}/a244e.svg`,
  radio: `${BASE}/1ccc7.svg`,

  // Hairline divider (1px rule used inside panels)
  divider: `${BASE}/261e4.svg`,

  // Navigation chrome and notification feedback
  menu: `${BASE}/menu.svg`,
  close: `${BASE}/close.svg`,
  check: `${BASE}/check.svg`,
  info: `${BASE}/info.svg`,
};

export const trendLegend = [
  { icon: `${BASE}/0f068.svg`, label: "Sleep" },
  { icon: `${BASE}/5802a.svg`, label: "Target" },
  { icon: `${BASE}/69bc2.svg`, label: "Alert threshold" },
];
