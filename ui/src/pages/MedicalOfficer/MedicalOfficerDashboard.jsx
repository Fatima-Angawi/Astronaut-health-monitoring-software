import { useState } from "react";
import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionStat from "../../components/layout/MissionStat";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import CrewMemberCard from "../../components/common/CrewMemberCard";
import AlertQueue from "../../features/alerts/AlertQueue";
import CriticalTask from "../../features/crew/CriticalTask";
import CrewRiskTimeline from "../../features/timeline/CrewRiskTimeline";
import { icons } from "../../data/icons";
import { medicalSections } from "../../data/navigation";
import {
  medicalMission,
  medicalCrew,
  alertQueue,
  criticalTask,
  riskTimeline,
} from "../../data/medicalOfficer";

const brand = {
  icon: icons.medicalNav,
  title: "Medical Dashboard",
  subtitle: "Crew Health Monitoring",
};

/**
 * Crew Medical Officer dashboard — crew-wide triage.
 *
 * Every severity here is a Rules Engine verdict carried through from the data layer;
 * nothing in this component evaluates or assigns medical severity.
 */
export default function MedicalOfficerDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard");
  const [selectedCrew, setSelectedCrew] = useState("A2");

  return (
    <DashboardLayout
      brand={brand}
      sections={medicalSections}
      activeSection={activeSection}
      onSectionChange={setActiveSection}
      title="Crew Medical Overview"
      meta={
        <>
          <div>
            <span>Open Alerts</span>
            <StatusBadge tone="red">
              {String(medicalMission.openAlerts).padStart(2, "0")}
            </StatusBadge>
          </div>
          <MissionStat label="Crew members" value={`${medicalCrew.length} Members`} />
          <MissionStat
            label="Mission"
            value={medicalMission.mission}
            hint={`Mission Day ${medicalMission.missionDay}`}
          />
        </>
      }
    >
      <section aria-labelledby="crew-status-title">
        <SectionHeader title="Crew Status" id="crew-status-title" />
        <div className="crew-grid">
          {medicalCrew.map((member) => (
            <CrewMemberCard
              key={member.code}
              member={member}
              selected={selectedCrew === member.code}
              onSelect={setSelectedCrew}
            />
          ))}
        </div>
      </section>

      <div className="detail-grid">
        <div className="detail-column">
          <AlertQueue alerts={alertQueue} />
          <CriticalTask task={criticalTask} />
        </div>

        <CrewRiskTimeline
          crew={medicalCrew}
          selectedCode={selectedCrew}
          onSelect={setSelectedCrew}
          timeline={riskTimeline}
        />
      </div>
    </DashboardLayout>
  );
}
