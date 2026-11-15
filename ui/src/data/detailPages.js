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
const heart = (metric, title, subtitle, unit, domain = ["auto", "auto"]) => ({ metric, title, subtitle: `${subtitle} · chart choice: team design`, unit, domain });
const HEART_CHARTS = [
  heart("hr_resting", "Resting heart rate", "Beats per minute", "bpm"),
  heart("exercise_minutes", "Exercise", "Minutes per day", "min", [0, "auto"]),
  heart("exercise_load_x_bw", "Exercise load", "Multiples of body weight", "x body weight", [0, "auto"]),
  heart("bp_systolic", "Blood pressure, systolic", "mmHg", "mmHg"),
  heart("bp_diastolic", "Blood pressure, diastolic", "mmHg", "mmHg"),
  heart("spo2", "Blood oxygen (SpO2)", "Percent", "%"),
  heart("body_weight", "Body weight", "Kilograms", "kg"),
  heart("fall_or_impact_event", "Fall or impact event", "1 = event on that day", "", [0, 1]),
];

export const PAGES = {
  sleep: { title: "Sleep and Workload", intro: "Sleep and work hours over time, with the alerts they feed.", trends: [SLEEP, SLEEP_NIGHT, WORK], indicators: ["R01", "R01f"] },
  reaction: { title: "Reaction Test", intro: "Reaction test history and the alerts it feeds. You can run a new test here.", trends: [PVT, PVT_SLOW], indicators: ["R01c"], withReactionTest: true },
  mood: { title: "Mood and Sleepiness", intro: "Self-reported mood and sleepiness over time.", trends: [MOOD, KSS], indicators: ["R02e"] },
  activity: { title: "Activity and Heart", intro: "Heart, blood pressure, oxygen, exercise and body measures over time. Which charts appear here is a team design choice.", trends: HEART_CHARTS, indicators: [], unmapped: true },
  crew: { title: "Crew Member Trends", intro: "Pick an astronaut in the header to see their history.", trends: [SLEEP, PVT, MOOD, WORK], indicators: ["R01", "R01c", "R01f", "R02e"] },
};
