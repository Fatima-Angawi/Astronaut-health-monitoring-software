import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionControls from "../../components/layout/MissionControls";
import MetricCard from "../../components/common/MetricCard";
import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";
import Async from "../../components/common/Async";
import HealthTrend from "../../features/trends/HealthTrend";
import ReactionTest from "../../features/reaction/ReactionTest";
import CheckinForm from "../../features/checkin/CheckinForm";
import EpisodeCard from "../../features/alerts/EpisodeCard";
import RecommendedActions from "../../features/alerts/RecommendedActions";
import MissionContext from "../../features/context/MissionContext";
import useApi from "../../hooks/useApi";
import { getEnvironmentDaily, getEpisodes, getSummary } from "../../api";
import { useAppState } from "../../state/context";
import { icons } from "../../data/icons";
import { clock, fixed } from "../../lib/format";

const brand = {
  icon: icons.logo,
  logo: true,
  title: "Astronaut Health",
  subtitle: "Personal Health Overview",
};

/** Sleep target and alert limit are shown with the Value ID that sets each (V005, V008). */
const TRENDS = [
  {
    metric: "sleep_h_7d_mean",
    title: "Sleep (7-day mean)",
    subtitle: "Hours per night · 8 h target (V005) · yellow below 6 h (V008, team design)",
    unit: "h",
    domain: [3, 10],
    lines: [
      { y: 8, label: "8 h target · V005", color: "#69c860" },
      { y: 6, label: "6 h · V008", color: "#fc743b" },
    ],
  },
  { metric: "pvt_lapses", title: "Reaction Test (PVT)", subtitle: "Lapses per test · dashed line is the astronaut's own baseline", unit: "lapses", domain: [0, "auto"] },
  { metric: "mood", title: "Mood", subtitle: "Self-reported · scale 1–5", unit: "/ 5", domain: [1, 5] },
];

/**
 * Astronaut screen: the selected astronaut's level, alerts (with sources and acknowledge),
 * key readings, trends, check-in, reaction test and mission context. Every value is read
 * through src/api.js; severity is exactly what the engine returned.
 */
export default function AstronautDashboard() {
  const { astronautId, day } = useAppState();
  const ready = day > 0;
  const summary = useApi(() => getSummary(astronautId, day), [astronautId, day], ready);
  const episodes = useApi(
    () => getEpisodes({ astronautId, day, minLevel: "yellow", open: 0, includeCabin: 1 }),
    [astronautId, day],
    ready,
  );
  const dose = useApi(() => getEnvironmentDaily("absorbed_dose_uGy_day", day, day), [day], ready);

  return (
    <DashboardLayout
      brand={brand}
      title="Health Overview"
      meta={
        <>
          <MissionControls />
        </>
      }
    >
      {!ready ? (
        <p className="async-note">The mission has not started yet (day 0). Pick a day, or start the mission clock.</p>
      ) : (
        <>
          <Async state={episodes}>
            {(d) =>
              d.items.length === 0 ? (
                <section className="alert-card">
                  <div className="alert-heading">
                    <h2>No active alerts for {astronautId}</h2>
                    <StatusBadge tone="green">Normal</StatusBadge>
                  </div>
                  <p>The engine reports nothing at yellow or above on day {day}.</p>
                </section>
              ) : (
                d.items.map((ep) => <EpisodeCard key={`${ep.indicator_id}-${ep.start_day}-${ep.is_cabin}`} episode={ep} />)
              )
            }
          </Async>

          <Async state={summary}>
            {(s) => <Metrics cards={s.cards} />}
          </Async>

          <div className="dashboard-grid">
            <Panel className="trends-panel">
              <h2>Health Trends - Last 14 Days</h2>
              {TRENDS.map((t) => (
                <HealthTrend key={t.metric} {...t} />
              ))}
            </Panel>

            <div className="right-column">
              <CheckinForm />
              <ReactionTest />
              <Async state={episodes}>{(d) => <RecommendedActions episodes={d.items} />}</Async>
              <Async state={summary}>
                {(s) => <MissionContext items={contextItems(s, dose.data?.items?.[0])} />}
              </Async>
            </div>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}

function Metrics({ cards }) {
  const base = (c) => (c.baseline ? `own baseline ${fixed(c.baseline.median)} (days 1–14)` : "");
  const eva = cards.next_critical_event;
  return (
    <section className="metrics">
      <MetricCard
        icon={icons.timer}
        status="Reaction test"
        tone="neutral"
        title="Reaction Test"
        to="/astronaut/reaction"
        value={cards.pvt_lapses ? `${fixed(cards.pvt_lapses.value, 0)} lapses` : "no data"}
        detail={cards.pvt_lapses ? `Day ${cards.pvt_lapses.mission_day} · ${base(cards.pvt_lapses)}` : ""}
      />
      <MetricCard
        icon={icons.moon}
        status="7-day mean"
        tone="neutral"
        title="Sleep"
        to="/astronaut/sleep"
        value={cards.sleep_h_7d_mean ? `${fixed(cards.sleep_h_7d_mean.value)} h` : "no data"}
        detail="Target 8 h · V005"
      />
      <MetricCard
        icon={icons.rocket}
        status={eva ? eva.type : "None"}
        tone="neutral"
        title="Next critical task"
        value={eva ? clock(eva.start_time) : "none planned"}
        detail={eva ? `Mission Day ${eva.mission_day} · in ${eva.days_until} day(s) · crew schedule (simulated)` : ""}
      />
      <MetricCard
        icon={icons.brain}
        status="Self-report"
        tone="neutral"
        title="Mood"
        to="/astronaut/mood"
        value={cards.mood ? `${fixed(cards.mood.value, 0)} / 5` : "no data"}
        detail={cards.mood ? `Day ${cards.mood.mission_day} · ${base(cards.mood)}` : ""}
      />
    </section>
  );
}

function contextItems(summary, doseRow) {
  const c = summary.context ?? {};
  const items = [
    {
      id: "space-weather",
      icon: icons.sun,
      title: "Space Weather",
      value: c.spe_active ? "SPE active" : "No SPE",
      detail: c.spe_active ? `Channel ≥ ${c.spe_channel_min_mev} MeV` : "NASA DONKI",
      source: "nasa",
    },
  ];
  const eva = summary.cards?.next_critical_event;
  items.push({
    id: "eva",
    icon: icons.calendar,
    title: eva ? `Next ${eva.type}` : "Next critical task",
    value: eva ? clock(eva.start_time) : "none",
    detail: eva ? `Day ${eva.mission_day} · simulated schedule` : "simulated schedule",
    source: "simulated",
  });
  items.push({
    id: "dose",
    icon: icons.dose,
    title: "ISS Dose Today",
    value: doseRow ? `${(doseRow.value / 1000).toFixed(2)} mGy` : "no data",
    detail: doseRow ? `${doseRow.source}${doseRow.value_id ? ` · ${doseRow.value_id}` : ""}` : "",
    source: doseRow?.is_real ? "nasa" : "simulated",
  });
  items.push({
    id: "co2",
    icon: icons.radio,
    title: "Cabin CO₂",
    value: c.cabin_co2 ? `${Math.round(c.cabin_co2.ppm).toLocaleString("en-US")} ppm` : "no data",
    detail: c.cabin_co2?.is_real ? "NASA" : "Simulated data",
    source: c.cabin_co2?.is_real ? "nasa" : "simulated",
  });
  return items;
}
