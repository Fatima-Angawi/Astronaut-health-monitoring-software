import StatusBadge from "./StatusBadge";

/**
 * Compact health metric tile: icon, status tag, label, value and a small unit/detail line.
 * `value` must already carry its unit (e.g. "4.8 h"), as supplied by the data source.
 */
export default function MetricCard({ icon, status, tone = "red", title, value, detail }) {
  return (
    <article className="metric">
      <div className="metric-top">
        <img src={icon} alt="" />
        <StatusBadge tone={tone}>{status}</StatusBadge>
      </div>
      <p className="label">{title}</p>
      <p className="metric-value">{value}</p>
      <p className="micro">{detail}</p>
    </article>
  );
}
