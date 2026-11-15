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
