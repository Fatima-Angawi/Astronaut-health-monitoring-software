import DashboardLayout from "../../components/layout/DashboardLayout";
import MissionControls from "../../components/layout/MissionControls";
import MissionStat from "../../components/layout/MissionStat";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import CrewMemberCard from "../../components/common/CrewMemberCard";
import Async from "../../components/common/Async";
import AlertQueue from "../../features/alerts/AlertQueue";
import CriticalTask from "../../features/crew/CriticalTask";
import CrewRiskTimeline from "../../features/timeline/CrewRiskTimeline";
import useApi from "../../hooks/useApi";
import { getEpisodes, getEvents, getStatus } from "../../api";
import { useAppState } from "../../state/context";
import { icons } from "../../data/icons";
import { LEVEL_RANK, dataThrough, label, roleLabel, tone } from "../../lib/format";

const brand = {
  icon: icons.medicalNav,
  title: "Medical Dashboard",
  subtitle: "Crew Health Monitoring",
};

const worst = (list) => [...list].sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level])[0];

/**
 * Crew Medical Officer screen: crew grid (level and standing level per astronaut), alert queue
 * incl. cabin alerts, next critical task and the selected astronaut's alert timeline.
 * Severity is the engine's; nothing is evaluated here.
 */
export default function MedicalOfficerDashboard() {
  const { astronautId, setAstronautId, day, mission } = useAppState();
  const ready = day > 0;
  const status = useApi(() => getStatus(day), [day], ready);
  const episodes = useApi(() => getEpisodes({ day, minLevel: "yellow", open: 0, includeCabin: 1 }), [day], ready);
  const events = useApi(() => getEvents(astronautId, day, mission?.days ?? 180), [astronautId, day, mission?.days], ready);

  const crew = (status.data?.items ?? []).map((m) => ({
    code: m.astronaut_id,
    name: roleLabel(m.role),
    role: `${m.n_alerts} alert(s)`,
    // the card shows the worse of today's level and the standing level (a standing alert is an open condition)
    status: LEVEL_RANK[m.standing_level] > LEVEL_RANK[m.level] ? `Standing ${label(m.standing_level)}` : label(m.level),
    tone: tone(LEVEL_RANK[m.standing_level] > LEVEL_RANK[m.level] ? m.standing_level : m.level),
    reason: m.top_reason,
  }));
  const all = episodes.data?.items ?? [];

  return (
    <DashboardLayout
      brand={brand}
      title="Crew Medical Overview"
      meta={
        <>
          <MissionControls />
          <div>
            <span>Open Alerts</span>
            <StatusBadge tone={all.length ? "red" : "green"}>{String(all.length).padStart(2, "0")}</StatusBadge>
          </div>
          <MissionStat label="Crew members" value={`${crew.length} Members`} />
        </>
      }
    >
      {!ready ? (
        <p className="async-note">The mission has not started yet (day 0).</p>
      ) : (
        <>
          <section aria-labelledby="crew-status-title">
            <SectionHeader title="Crew Status" id="crew-status-title" />
            <Async state={status}>
              {() => (
                <div className="crew-grid">
                  {crew.map((member) => (
                    <CrewMemberCard
                      key={member.code}
                      member={member}
                      selected={astronautId === member.code}
                      onSelect={setAstronautId}
                    />
                  ))}
                </div>
              )}
            </Async>
          </section>

          <div className="detail-grid">
            <div className="detail-column">
              <Async state={episodes}>{(d) => <AlertQueue episodes={d.items} />}</Async>
              <Async state={events}>
                {(d) => (
                  <CriticalTask
                    astronautId={astronautId}
                    event={d.items.find((e) => e.critical && e.mission_day >= day)}
                    episode={worst(all.filter((e) => e.astronaut_id === astronautId && !e.is_cabin)) ?? null}
                  />
                )}
              </Async>
            </div>

            <CrewRiskTimeline
              crew={crew}
              selectedCode={astronautId}
              onSelect={setAstronautId}
              episodes={all.filter((e) => e.astronaut_id === astronautId)}
              day={day}
              sentThrough={dataThrough(mission)}
            />
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
