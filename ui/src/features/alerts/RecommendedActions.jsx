import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { icons } from "../../data/icons";
import { label, tone } from "../../lib/format";

/**
 * Actions are the engine's own action text for each alert episode (guidance layer), with the
 * level of the alert they belong to. Nothing is invented or evaluated in the browser.
 */
export default function RecommendedActions({ episodes }) {
  const seen = new Set();
  const actions = episodes.filter((e) => e.action && !seen.has(e.action) && seen.add(e.action));

  return (
    <Panel className="actions-card">
      <SectionHeader title="Recommended Actions" />
      {actions.length === 0 && <p className="async-note">No actions: nothing is alerting.</p>}
      {actions.map((a) => (
        <div className="action-item" key={`${a.indicator_id}-${a.start_day}`}>
          <div className="action-title">
            <strong>{a.title}</strong>
            <img src={icons.actionWarning} alt="" />
          </div>
          <p>{a.action}</p>
          <StatusBadge tone={tone(a.level)}>{label(a.level)}</StatusBadge>
        </div>
      ))}
    </Panel>
  );
}
