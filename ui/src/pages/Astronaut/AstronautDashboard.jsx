import { useState } from "react";
import DashboardLayout from "../../components/layout/DashboardLayout";
import AlertCard from "../../components/common/AlertCard";
import MetricCard from "../../components/common/MetricCard";
import Panel from "../../components/common/Panel";
import HealthTrend from "../../features/trends/HealthTrend";
import ReactionTest from "../../features/reaction/ReactionTest";
import RecommendedActions from "../../features/alerts/RecommendedActions";
import MissionContext from "../../features/context/MissionContext";
import { icons } from "../../data/icons";
import { astronautSections } from "../../data/navigation";
import {
  astronautMission,
  astronautAlert,
  astronautMetrics,
  astronautTrends,
  astronautActions,
  astronautContext,
} from "../../data/astronaut";

const brand = {
  icon: icons.logo,
  logo: true,
  title: "Astronaut Health",
  subtitle: "Personal Health Overview",
};

/**
 * Astronaut dashboard — the crew member's own health and mission overview.
 * All values come from src/data/astronaut.js (clearly labelled mock data); the alert
 * verdict is shown exactly as delivered by the backend Rules Engine.
 */
export default function AstronautDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard");
  const missionDay = String(astronautMission.missionDay).padStart(3, "0");

  return (
    <DashboardLayout
      brand={brand}
      sections={astronautSections}
      activeSection={activeSection}
      onSectionChange={setActiveSection}
      title="Health Overview"
      meta={
        <>
          <div className="mission-stat--optional">
            <span>Mission Status</span>
            <strong className="on-track">
              {astronautMission.status}
              <img src={icons.status} alt="" />
            </strong>
          </div>
          <div>
            <span>Mission Day</span>
            <strong>
              {astronautMission.missionLength} / {missionDay}
            </strong>
          </div>
        </>
      }
    >
      <AlertCard
        title={astronautAlert.title}
        body={astronautAlert.body}
        severity={astronautAlert.severity}
        tone={astronautAlert.tone}
        severitySource={astronautAlert.severitySource}
        recommendationLabel={astronautAlert.recommendationLabel}
        recommendation={astronautAlert.recommendation}
      />

      <section className="metrics">
        {astronautMetrics.map((metric) => (
          <MetricCard key={metric.id} {...metric} />
        ))}
      </section>

      <div className="dashboard-grid">
        <Panel className="trends-panel">
          <h2>Health Trends - Last 14 Days</h2>
          {astronautTrends.map((trend) => (
            <HealthTrend key={trend.id} {...trend} />
          ))}
        </Panel>

        <div className="right-column">
          <ReactionTest />
          <RecommendedActions actions={astronautActions} />
          <MissionContext items={astronautContext} />
        </div>
      </div>
    </DashboardLayout>
  );
}
