import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";
import DataQualityBadge from "../../components/common/DataQualityBadge";

/**
 * Ground-side summary of the latest downlinked crew report.
 *
 * The link was delayed, so the coverage window is reported as provisional through
 * `DataQualityBadge` — a partial window is never shown as a complete record.
 */
export default function LinkReportCard({ report }) {
  return (
    <Panel className="report-card" aria-labelledby="link-report-title">
      <div className="panel-heading">
        <h2 id="link-report-title">{report.title}</h2>
        <StatusBadge tone={report.tone}>{report.status}</StatusBadge>
      </div>

      <div className="report-details">
        <p>
          <strong>Mission</strong>
          <span>{report.mission}</span>
        </p>
        <p>
          <strong>Report Coverage</strong>
          <span>{report.coverage}</span>
        </p>
        <p>
          <strong>Priority Case</strong>
          <StatusBadge tone={report.priorityCase.tone}>
            {report.priorityCase.code} · {report.priorityCase.severity}
          </StatusBadge>
        </p>
      </div>

      <div className="report-quality">
        <DataQualityBadge
          status={report.quality.status}
          label={report.quality.label}
          detail={report.quality.detail}
        />
      </div>
    </Panel>
  );
}
