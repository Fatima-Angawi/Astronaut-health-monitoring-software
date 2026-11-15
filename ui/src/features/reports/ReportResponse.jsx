import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";

/** One titled column of findings inside the report response panel. */
function FindingColumn({ title, badge, findings }) {
  return (
    <div className="response-column">
      <h3>{title}</h3>
      <StatusBadge tone={badge.tone}>{badge.label}</StatusBadge>
      <div className="finding-list">
        {findings.map((finding) => (
          <p key={finding}>{finding}</p>
        ))}
      </div>
    </div>
  );
}

/**
 * What the crew reported doing in response, next to the system-detected findings.
 *
 * Note: the original page repeated the "Delayed Link Report" heading here; this panel is
 * the response section of that report, so it carries its own title instead.
 */
export default function ReportResponse({ response, system }) {
  return (
    <Panel className="delayed-card" aria-labelledby="report-response-title">
      <div className="panel-heading">
        <h2 id="report-response-title">Report Response</h2>
      </div>
      <div className="response-grid">
        <FindingColumn title={response.title} badge={response.badge} findings={response.findings} />
        <FindingColumn title={system.title} badge={system.badge} findings={system.findings} />
      </div>
    </Panel>
  );
}
