import { icons } from "./icons";

/**
 * The three role dashboards, used by the shared sidebar for cross-dashboard navigation.
 * Keep in sync with the routes declared in src/App.jsx.
 */
export const dashboardRoutes = [
  { id: "astronaut", path: "/astronaut", label: "Astronaut", icon: icons.astronautNav },
  {
    id: "medical-officer",
    path: "/medical-officer",
    label: "Crew Medical Officer",
    icon: icons.medicalNav,
  },
  {
    id: "flight-surgeon",
    path: "/flight-surgeon",
    label: "Flight Surgeon",
    icon: icons.surgeonNav,
  },
];

/** In-page sections for the Astronaut dashboard sidebar. */
export const astronautSections = [
  { id: "dashboard", label: "Dashboard", icon: icons.dashboardNav },
  { id: "sleep", label: "Sleep", icon: icons.sleepNav },
  { id: "activity", label: "Activity", icon: icons.activityNav },
  { id: "heart", label: "Heart", icon: icons.heartNav },
  { id: "settings", label: "Settings", icon: icons.settingsNav },
];

/** In-page sections for the Crew Medical Officer dashboard sidebar. */
export const medicalSections = [
  { id: "dashboard", label: "Dashboard", icon: icons.dashboardNav },
  { id: "night", label: "Night mode", icon: icons.sleepNav },
  { id: "activity", label: "Activity", icon: icons.activityNav },
  { id: "health", label: "Health", icon: icons.heartNav },
  { id: "settings", label: "Settings", icon: icons.settingsNav },
];

/** In-page sections for the Flight Surgeon dashboard sidebar. */
export const surgeonSections = [
  { id: "dashboard", label: "Dashboard", icon: icons.dashboardNav },
  { id: "sleep", label: "Sleep monitoring", icon: icons.sleepNav },
  { id: "vitals", label: "Vital activity", icon: icons.activityNav },
  { id: "crew-health", label: "Crew health", icon: icons.heartNav },
  { id: "settings", label: "Settings", icon: icons.settingsNav },
];
