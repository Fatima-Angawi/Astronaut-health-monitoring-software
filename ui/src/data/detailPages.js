/**
 * Charts and engine indicators of each detail page. Metric names are those of /metrics;
 * reference lines carry the Value ID that sets them (V005 sleep target, V008 sleep alert).
 */
const SLEEP = {
  metric: "sleep_h_7d_mean", title: "Sleep (7-day mean)", unit: "h", domain: [3, 10],
  subtitle: "8 h target (V005) · yellow below 6 h (V008, team design)",
  lines: [{ y: 8, label: "8 h target · V005", color: "#69c860" }, { y: 6, label: "6 h · V008", color: "#fc743b" }],
};
const SLEEP_NIGHT = { metric: "sleep_h", title: "Sleep per night", subtitle: "Hours per night", unit: "h", domain: [0, 11] };
const WORK = { metric: "work_hours", title: "Work hours", subtitle: "Hours per day", unit: "h", domain: [0, "auto"] };
const PVT = { metric: "pvt_lapses", title: "Reaction test lapses", subtitle: "Dashed line is the astronaut own baseline (days 1-14)", unit: "lapses", domain: [0, "auto"] };
const PVT_SLOW = { metric: "pvt_slowest10_ms", title: "Slowest 10 % of reactions", subtitle: "Milliseconds", unit: "ms", domain: ["auto", "auto"] };
const MOOD = { metric: "mood", title: "Mood", subtitle: "Self-reported, 1-5", unit: "/ 5", domain: [1, 5] };
const KSS = { metric: "kss", title: "Sleepiness (KSS)", subtitle: "Self-reported, 1-9", unit: "/ 9", domain: [1, 9] };
const EXERCISE = { metric: "exercise_minutes", title: "Exercise", subtitle: "Minutes per day", unit: "min", domain: [0, "auto"] };
const HR = { metric: "hr_resting", title: "Resting heart rate", subtitle: "Beats per minute", unit: "bpm", domain: ["auto", "auto"] };

export const PAGES = {
  sleep: { title: "Sleep and Workload", intro: "Sleep and work hours over time, with the alerts they feed.", trends: [SLEEP, SLEEP_NIGHT, WORK], indicators: ["R01", "R01f"] },
  reaction: { title: "Reaction Test", intro: "Reaction test history and the alerts it feeds. You can run a new test here.", trends: [PVT, PVT_SLOW], indicators: ["R01c"], withReactionTest: true },
  mood: { title: "Mood and Sleepiness", intro: "Self-reported mood and sleepiness over time.", trends: [MOOD, KSS], indicators: ["R02e"] },
  activity: { title: "Activity and Heart", intro: "Exercise and resting heart rate over time.", trends: [EXERCISE, HR], indicators: [] },
  crew: { title: "Crew Member Trends", intro: "Pick an astronaut in the header to see their history.", trends: [SLEEP, PVT, MOOD, WORK], indicators: ["R01", "R01c", "R01f", "R02e"] },
};
