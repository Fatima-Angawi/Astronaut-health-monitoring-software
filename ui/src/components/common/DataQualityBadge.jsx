import StatusBadge from "./StatusBadge";

/**
 * Makes data coverage / completeness explicit next to a summary or a chart.
 * Incomplete or delayed data must never be presented as a fully reliable record.
 *
 * status: "complete" | "partial" | "delayed" | "illustrative"
 */
const QUALITY = {
  complete: { tone: "green", defaultLabel: "Complete" },
  partial: { tone: "yellow", defaultLabel: "Partial" },
  delayed: { tone: "yellow", defaultLabel: "Delayed" },
  illustrative: { tone: "neutral", defaultLabel: "Illustrative" },
};

export default function DataQualityBadge({ status = "complete", label, detail }) {
  const quality = QUALITY[status] ?? QUALITY.complete;
  return (
    <span className="quality-badge">
      <StatusBadge tone={quality.tone} title={detail}>
        {label ?? quality.defaultLabel}
      </StatusBadge>
      {detail && <small className="quality-badge__detail">{detail}</small>}
    </span>
  );
}
