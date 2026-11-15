import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";
import DataSourceBadge from "../../components/common/DataSourceBadge";

/**
 * Headline clinical alert shown to the flight surgeon.
 *
 * Severity is printed verbatim — it is the verdict of the backend Rules Engine, and the
 * frontend never re-derives thresholds or triage.
 */
export default function CriticalMedicalAlert({ alert }) {
  return (
    <Panel className="critical-card" aria-labelledby="critical-alert-title">
      <div className="panel-heading">
        <h2 id="critical-alert-title">{alert.title}</h2>
        <StatusBadge tone={alert.tone}>{alert.severity}</StatusBadge>
      </div>

      <div className="critical-details">
        <strong>{alert.headline}</strong>
        <p>{alert.body}</p>
        <strong>{alert.followUp}</strong>
      </div>

      {alert.severitySource && (
        <div className="alert-source">
          <span>Severity source</span>
          <DataSourceBadge kind="engine" label={alert.severitySource} />
        </div>
      )}
    </Panel>
  );
}
