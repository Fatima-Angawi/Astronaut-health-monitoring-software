import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";

/**
 * Alert-driven recommendations for the astronaut. The list and its priorities come from
 * the backend guidance layer, not from conditions evaluated in the browser.
 */
export default function RecommendedActions({ actions, priority = "High Priority" }) {
  return (
    <Panel className="actions-card">
      <SectionHeader
        title="Recommended Actions"
        action={<StatusBadge tone="red">{priority}</StatusBadge>}
      />
      {actions.map((action) => (
        <div className="action-item" key={action.id}>
          <div className="action-title">
            <strong>{action.title}</strong>
            <img src={action.icon} alt="" />
          </div>
          <p>{action.copy}</p>
          <StatusBadge tone={action.tone}>{action.tag}</StatusBadge>
        </div>
      ))}
    </Panel>
  );
}
