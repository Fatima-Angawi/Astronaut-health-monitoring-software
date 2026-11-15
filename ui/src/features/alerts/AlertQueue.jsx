import Panel from "../../components/common/Panel";
import Divider from "../../components/common/Divider";
import StatusBadge from "../../components/common/StatusBadge";
import { label, LEVEL_RANK, tone } from "../../lib/format";

/**
 * Open alert queue for the crew, worst first. Each row is an engine episode: the affected
 * astronaut (or "Cabin"), its plain-language title and the engine's level.
 */
export default function AlertQueue({ episodes, title = "Alert Queue" }) {
  const rows = [...episodes].sort((a, b) => LEVEL_RANK[b.level] - LEVEL_RANK[a.level]);
  return (
    <Panel className="alert-panel" aria-labelledby="alert-queue-title">
      <h2 id="alert-queue-title" className="section-heading__title">
        {title}
      </h2>
      <Divider />
      <div className="alert-list">
        {rows.length === 0 && <p className="async-note">No alerts at yellow or above.</p>}
        {rows.map((e) => (
          <div className="alert-row" key={`${e.astronaut_id}-${e.indicator_id}-${e.start_day}-${e.is_cabin}`}>
            <span className="alert-row__label">
              <strong>{e.is_cabin ? "Cabin" : e.astronaut_id}</strong>
              <span aria-hidden="true"> · </span>
              {e.title ?? e.indicator_id}
            </span>
            <StatusBadge tone={tone(e.level)}>{label(e.level)}</StatusBadge>
          </div>
        ))}
      </div>
    </Panel>
  );
}
