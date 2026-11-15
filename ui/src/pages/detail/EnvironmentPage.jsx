import DetailShell from "./DetailShell";
import Async from "../../components/common/Async";
import Panel from "../../components/common/Panel";
import DataSourceBadge from "../../components/common/DataSourceBadge";
import EnvTrend from "../../components/common/EnvTrend";
import EpisodeCard from "../../features/alerts/EpisodeCard";
import useApi from "../../hooks/useApi";
import { getEnvironmentDaily, getEpisodes, getSpaceWeather } from "../../api";
import { useAppState } from "../../state/context";

/** Radiation and cabin: daily environment series, solar particle events (NASA DONKI), cabin alerts. */
export default function EnvironmentPage({ role }) {
  const { day } = useAppState();
  const ready = day > 0;
  const metrics = useApi(() => getEnvironmentDaily(), [], true);
  const spe = useApi(() => getSpaceWeather(), [], true);
  const cabin = useApi(() => getEpisodes({ day, minLevel: "yellow", open: 0, includeCabin: 1 }), [day], ready);
  const from = Math.max(1, (day ?? 1) - 29);

  return (
    <DetailShell
      role={role}
      title="Radiation and Cabin"
      showAstronaut={false}
      intro="Daily values for the 30 days up to the selected day, and the solar particle events seen so far."
    >
      {!ready ? (
        <p className="async-note">The mission has not started yet (day 0).</p>
      ) : (
        <>
          <Async state={cabin}>
            {(d) => d.items.filter((e) => e.is_cabin).map((e) => <EpisodeCard key={`${e.indicator_id}-${e.start_day}`} episode={e} />)}
          </Async>
          <Panel className="trends-panel detail-panel">
            <Async state={metrics}>
              {(m) => {
                const eda = m.items.filter((x) => /EDA/i.test(x.source));
                return (
                  <>
                    {m.items.map((x) => (
                      <EnvTrend key={`${x.metric}-${x.source}`} metric={x.metric} source={x.source} unit={x.unit} from={from} to={day} />
                    ))}
                    {eda.length > 0 && (
                      <p className="pvt-note">
                        Cabin environment from EDA: mission days {Math.min(...eda.map((x) => x.first_day))}–
                        {Math.max(...eda.map((x) => x.last_day))}.
                      </p>
                    )}
                  </>
                );
              }}
            </Async>
          </Panel>
          <Panel className="actions-card">
            <h2>Solar particle events</h2>
            <Async state={spe}>
              {(d) => {
                const seen = d.items.filter((e) => e.mission_day !== null && e.mission_day <= day);
                return seen.length === 0 ? (
                  <p className="async-note">No solar particle event up to day {day}.</p>
                ) : (
                  seen.map((e) => (
                    <div className="action-item" key={e.event_key}>
                      <div className="action-title">
                        <strong>
                          Day {e.mission_day} · {e.max_channel}
                        </strong>
                      </div>
                      <p>
                        Onset {e.onset_time} ·{" "}
                        <a href={e.source_link} target="_blank" rel="noreferrer">
                          NASA DONKI
                        </a>
                      </p>
                      <DataSourceBadge kind="nasa" label={`NASA · ${e.value_id}`} />
                    </div>
                  ))
                );
              }}
            </Async>
          </Panel>
        </>
      )}
    </DetailShell>
  );
}
