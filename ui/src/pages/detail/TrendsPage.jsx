import { useState } from "react";
import DetailShell from "./DetailShell";
import Panel from "../../components/common/Panel";
import Async from "../../components/common/Async";
import HealthTrend from "../../features/trends/HealthTrend";
import EpisodeCard from "../../features/alerts/EpisodeCard";
import ReactionTest from "../../features/reaction/ReactionTest";
import useApi from "../../hooks/useApi";
import { getEpisodes } from "../../api";
import { useAppState } from "../../state/context";

const WINDOWS = [14, 30, 60, 180];

/**
 * Detail page for one part of the dashboard: longer history charts for the selected astronaut
 * plus the engine alerts that belong to it (filtered by indicator id), with their sources.
 * `trends` are HealthTrend props; `indicators` are the engine indicators shown here.
 */
export default function TrendsPage({ role, title, intro, trends, indicators = [], withReactionTest = false }) {
  const { astronautId, day } = useAppState();
  const [window, setWindow] = useState(30);
  const ready = day > 0;
  const episodes = useApi(
    () => getEpisodes({ astronautId, day, minLevel: "yellow", open: 0, includeCabin: 0 }),
    [astronautId, day],
    ready,
  );

  return (
    <DetailShell role={role} title={title} intro={intro}>
      {!ready ? (
        <p className="async-note">The mission has not started yet (day 0).</p>
      ) : (
        <>
          <Panel className="trends-panel detail-panel">
            <div className="window-select" role="group" aria-label="History window">
              <span>History</span>
              {WINDOWS.map((w) => (
                <button key={w} type="button" className={w === window ? "active" : ""} onClick={() => setWindow(w)}>
                  {w === 180 ? "All" : `${w} d`}
                </button>
              ))}
            </div>
            {trends.map((t) => (
              <HealthTrend key={t.metric} {...t} window={window} />
            ))}
          </Panel>

          {indicators.length > 0 && (
            <Async state={episodes}>
              {(d) => {
                const mine = d.items.filter((e) => indicators.includes(e.indicator_id));
                return mine.length === 0 ? (
                  <p className="async-note">No alerts for {astronautId} in this area on day {day}.</p>
                ) : (
                  mine.map((e) => <EpisodeCard key={`${e.indicator_id}-${e.start_day}`} episode={e} />)
                );
              }}
            </Async>
          )}
          {withReactionTest && <ReactionTest />}
        </>
      )}
    </DetailShell>
  );
}
