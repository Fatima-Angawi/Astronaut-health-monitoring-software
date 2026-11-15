import { icons } from "./icons";

/**
 * The three role dashboards, used by the navbar switcher and sidebar role lookup.
 * Keep in sync with the routes declared in src/App.jsx.
 */
export const dashboardRoutes = [
  {
    id: "astronaut",
    path: "/astronaut",
    label: "Astronaut Health",
    subtitle: "Personal Health Overview",
    icon: icons.astronautNav,
    iconTone: "nav",
    brandIcon: icons.logo,
    brandTone: "nav",
    brandMark: "logo",
  },
  {
    id: "medical-officer",
    path: "/medical-officer",
    label: "Medical Dashboard",
    subtitle: "Crew Medical Overview",
    icon: icons.medicalNav,
    iconTone: "medical",
    brandIcon: icons.medicalNav,
    brandTone: "medical",
    brandMark: "icon",
  },
  {
    id: "flight-surgeon",
    path: "/flight-surgeon",
    label: "Flight Surgeon Center",
    subtitle: "Ground Medical Operations",
    icon: icons.surgeonNav,
    iconTone: "surgeon",
    brandIcon: icons.surgeonNav,
    brandTone: "surgeon",
    brandMark: "icon",
  },
];

/**
 * Second group of the sidebar: the detail pages of the current screen. Each opens a page with
 * the full history and the alerts behind one part of the dashboard.
 */
export const sectionRoutes = {
  astronaut: [
    { id: "overview", path: "/astronaut", label: "Dashboard", icon: icons.dashboardNav, end: true },
    { id: "sleep", path: "/astronaut/sleep", label: "Sleep and workload", icon: icons.sleepNav },
    { id: "reaction", path: "/astronaut/reaction", label: "Reaction test", icon: icons.timer },
    { id: "mood", path: "/astronaut/mood", label: "Mood and sleepiness", icon: icons.brain },
    { id: "activity", path: "/astronaut/activity", label: "Activity and heart", icon: icons.heartNav },
    { id: "environment", path: "/astronaut/environment", label: "Radiation and cabin", icon: icons.dose },
  ],
  "medical-officer": [
    { id: "overview", path: "/medical-officer", label: "Dashboard", icon: icons.dashboardNav, end: true },
    { id: "alerts", path: "/medical-officer/alerts", label: "All alerts", icon: icons.warning },
    { id: "crew", path: "/medical-officer/crew", label: "Crew member trends", icon: icons.heartNav },
    { id: "environment", path: "/medical-officer/environment", label: "Radiation and cabin", icon: icons.dose },
  ],
  "flight-surgeon": [
    { id: "overview", path: "/flight-surgeon", label: "Dashboard", icon: icons.dashboardNav, end: true },
    { id: "alerts", path: "/flight-surgeon/alerts", label: "All alerts", icon: icons.warning },
    { id: "summary", path: "/flight-surgeon/summary", label: "Crew summary", icon: icons.user },
    { id: "crew", path: "/flight-surgeon/crew", label: "Crew member trends", icon: icons.heartNav },
    { id: "environment", path: "/flight-surgeon/environment", label: "Radiation and cabin", icon: icons.dose },
  ],
};

export const brands = Object.fromEntries(
  dashboardRoutes.map((route) => [
    route.id,
    {
      icon: route.brandIcon,
      logo: route.brandMark === "logo",
      title: route.label,
      subtitle: route.subtitle,
    },
  ]),
);
