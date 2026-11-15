import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionControls from "../../components/layout/MissionControls";
import MissionStat from "../../components/layout/MissionStat";
import Async from "../../components/common/Async";
import LinkReportCard from "../../features/reports/LinkReportCard";
import CriticalMedicalAlert from "../../features/reports/CriticalMedicalAlert";
import ReportResponse from "../../features/reports/ReportResponse";
import CrewHealthSummary from "../../features/crew/CrewHealthSummary";
import useApi from "../../hooks/useApi";
import { getEpisodes, getEvents, getStatus, getSummary } from "../../api";
import { useAppState } from "../../state/context";
import { icons } from "../../data/icons";
import { LEVEL_RANK, clock, dataThrough, label, roleLabel, tone } from "../../lib/format";

const brand = {
  icon: icons.surgeonNav,
  title: "Flight Surgeon Center",
  subtitle: "Ground Medical Operations",
};

const worst = (list) => [...list].sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level])[0];

/**
 * Flight Surgeon screen: ground review of the crew's data up to the selected day. The data
 * window is stated next to the report; severity is the engine's, never re-derived here.
 */
export default function FlightSurgeonDashboard() {
  const { day, mission } = useAppState();
  const ready = day > 0;
  const status = useApi(() => getStatus(day), [day], ready);
  const episodes = useApi(() => getEpisodes({ day, minLevel: "yellow", open: 0, includeCabin: 1 }), [day], ready);
  const summaries = useApi(
    () => Promise.all(["A1", "A2", "A3", "A4"].map((id) => getSummary(id, day))),
    [day],
    ready,
  );
  const top = worst(status.data?.items ?? []);
  const events = useApi(
    () => getEvents(top?.astronaut_id, day, mission?.days ?? 180),
    [top?.astronaut_id, day, mission?.days],
    ready && Boolean(top),
  );

  return (
    <DashboardLayout
      brand={brand}
      title="Ground Medical Overview"
      meta={
        <>
          <MissionControls showAstronaut={false} />
          <MissionStat label="Crew members" value={`${status.data?.count ?? "-"} Members`} />
        </>
      }
    >
      {!ready ? (
        <p className="async-note">The mission has not started yet (day 0).</p>
      ) : (
        <Async state={status}>
          {(st) => {
            const eps = episodes.data?.items ?? [];
            const priority = top && top.level !== "none" ? top : null;
            const priorityEps = priority ? eps.filter((e) => e.astronaut_id === priority.astronaut_id && !e.is_cabin) : [];
            const lead = worst(priorityEps);
            const sent = dataThrough(mission);
            const partial = typeof sent === "number" && sent < day;
            const nextEvent = events.data?.items?.find((e) => e.critical && e.mission_day >= day);
            const crewRows = (summaries.data ?? []).map((s) => ({
              code: s.astronaut_id,
              name: roleLabel(s.status.role),
              status: label(s.status.level),
              tone: tone(s.status.level),
              sleep7dH: s.cards.sleep_h_7d_mean?.value,
            }));

            return (
              <>
                <div className="top-panels">
                  <LinkReportCard
                    report={{
                      title: "Crew Report",
                      status: partial ? "Partial" : "Received",
                      tone: partial ? "yellow" : "green",
                      mission: `Day ${day} of ${mission?.days ?? 180} · ${st.date}`,
                      coverage: `Days 1–${sent ?? day}`,
                      priorityCase: priority
                        ? { code: priority.astronaut_id, severity: label(priority.level).toUpperCase(), tone: tone(priority.level) }
                        : { code: "None", severity: "NORMAL", tone: "green" },
                      quality: {
                        status: partial ? "partial" : "complete",
                        label: partial ? "Data behind the selected day" : "Data up to date",
                        detail: `received through day ${sent ?? "?"}`,
                      },
                    }}
                  />
                  {lead ? (
                    <CriticalMedicalAlert
                      alert={{
                        title: "Critical Medical Alert",
                        severity: label(lead.level).toUpperCase(),
                        tone: tone(lead.level),
                        headline: lead.title ?? lead.indicator_id,
                        body: lead.first_reason,
                        followUp: nextEvent
                          ? `Upcoming ${nextEvent.type} · Day ${nextEvent.mission_day} · ${clock(nextEvent.start_time)} UTC`
                          : "No critical task planned",
                        severitySource: `Rules Engine · ${lead.indicator_id}`,
                      }}
                    />
                  ) : (
                    <CriticalMedicalAlert
                      alert={{
                        title: "Critical Medical Alert",
                        severity: "NORMAL",
                        tone: "green",
                        headline: "No active alert",
                        body: `The engine reports nothing at yellow or above for the crew on day ${day}.`,
                        followUp: "",
                        severitySource: "Rules Engine",
                      }}
                    />
                  )}
                </div>

                <div className="bottom-panels">
                  <ReportResponse
                    response={{
                      title: "Crew Response",
                      badge: { label: `${eps.filter((e) => e.acknowledged === 1).length} acknowledged`, tone: "green" },
                      findings: eps.length
                        ? eps.map((e) => `${e.is_cabin ? "Cabin" : e.astronaut_id} · ${e.title ?? e.indicator_id}: ${e.acknowledged === 1 ? "acknowledged" : "not yet acknowledged"}`)
                        : ["No alerts to acknowledge"],
                    }}
                    system={{
                      title: "System Findings",
                      badge: { label: priority ? priority.astronaut_id : "None", tone: priority ? tone(priority.level) : "green" },
                      findings: priorityEps.length
                        ? priorityEps.map((e) => e.first_reason)
                        : ["Nothing alerting"],
                    }}
                  />
                  <Async state={summaries}>{() => <CrewHealthSummary members={crewRows} />}</Async>
                </div>
              </>
            );
          }}
        </Async>
      )}
    </DashboardLayout>
  );
}
