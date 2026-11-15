import DetailShell from "./DetailShell";
import Async from "../../components/common/Async";
import EpisodeCard from "../../features/alerts/EpisodeCard";
import useApi from "../../hooks/useApi";
import { getEpisodes } from "../../api";
import { useAppState } from "../../state/context";
import { LEVEL_RANK } from "../../lib/format";

/** Every alert episode of the whole crew (and the cabin) on the selected day, worst first, with sources. */
export default function AlertsPage({ role }) {
  const { day } = useAppState();
  const state = useApi(() => getEpisodes({ day, minLevel: "yellow", open: 0, includeCabin: 1 }), [day], day > 0);
  return (
    <DetailShell
      role={role}
      title="All Alerts"
      showAstronaut={false}
      intro="Every alert the engine holds on the selected day, worst first. Open Why? to see the source behind each."
    >
      <Async state={state}>
        {(d) =>
          d.items.length === 0 ? (
            <p className="async-note">No alerts at yellow or above.</p>
          ) : (
            [...d.items]
              .sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level])
              .map((e) => (
                <EpisodeCard
                  key={`${e.astronaut_id}-${e.indicator_id}-${e.start_day}-${e.is_cabin}`}
                  episode={{ ...e, title: `${e.is_cabin ? "Cabin" : e.astronaut_id} · ${e.title ?? e.indicator_id}` }}
                />
              ))
          )
        }
      </Async>
    </DetailShell>
  );
}
