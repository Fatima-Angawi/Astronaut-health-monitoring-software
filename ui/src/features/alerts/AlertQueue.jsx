import Panel from "../../components/common/Panel";
import Divider from "../../components/common/Divider";
import StatusBadge from "../../components/common/StatusBadge";

/**
 * Open alert queue for the crew. Each entry shows the affected crew code and the severity
 * produced by the backend Rules Engine.
 */
export default function AlertQueue({ alerts, title = "Alert Queue" }) {
  return (
    <Panel className="alert-panel" aria-labelledby="alert-queue-title">
      <h2 id="alert-queue-title" className="section-heading__title">
        {title}
      </h2>
      <Divider />
      <div className="alert-list">
        {alerts.map((alert) => (
          <div className="alert-row" key={alert.id}>
            <span className="alert-row__label">
              <strong>{alert.code}</strong>
              <span aria-hidden="true"> · </span>
              {alert.title}
            </span>
            <StatusBadge tone={alert.tone}>{alert.status}</StatusBadge>
          </div>
        ))}
      </div>
    </Panel>
  );
}
