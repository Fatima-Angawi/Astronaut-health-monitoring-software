import { useState } from "react";
import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionStat from "../../components/layout/MissionStat";
import LinkReportCard from "../../features/reports/LinkReportCard";
import CriticalMedicalAlert from "../../features/reports/CriticalMedicalAlert";
import ReportResponse from "../../features/reports/ReportResponse";
import CrewHealthSummary from "../../features/crew/CrewHealthSummary";
import { icons } from "../../data/icons";
import { surgeonSections } from "../../data/navigation";
import {
  surgeonMission,
  delayedLinkReport,
  criticalMedicalAlert,
  crewResponse,
  systemFindings,
  surgeonCrew,
} from "../../data/flightSurgeon";

const brand = {
  icon: icons.surgeonNav,
  title: "Flight Surgeon Center",
  subtitle: "Ground Medical Operations",
};

/**
 * Flight Surgeon dashboard — ground review of downlinked crew reports.
 *
 * The coverage window is shown next to the report, and the delayed link is reported as a
 * partial-quality window rather than a complete record.
 */
export default function FlightSurgeonDashboard() {
  const [activeSection, setActiveSection] = useState("dashboard");

  return (
    <DashboardLayout
      brand={brand}
      sections={surgeonSections}
      activeSection={activeSection}
      onSectionChange={setActiveSection}
      title="Ground Medical Overview"
      meta={
        <>
          <MissionStat label="Mission" value={surgeonMission.mission} />
          <MissionStat
            label="Crew members"
            value={`${String(surgeonMission.crewCount).padStart(2, "0")} Members`}
          />
          <MissionStat label="Coverage" value={surgeonMission.coverageLabel} />
        </>
      }
    >
      <div className="top-panels">
        <LinkReportCard report={delayedLinkReport} />
        <CriticalMedicalAlert alert={criticalMedicalAlert} />
      </div>

      <div className="bottom-panels">
        <ReportResponse response={crewResponse} system={systemFindings} />
        <CrewHealthSummary members={surgeonCrew} />
      </div>
    </DashboardLayout>
  );
}
