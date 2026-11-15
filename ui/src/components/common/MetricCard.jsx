import { Link } from "react-router-dom";
import Icon from "./Icon";
import StatusBadge from "./StatusBadge";

/**
 * Compact health metric tile: icon, status tag, label, value and a small unit/detail line.
 * `value` must already carry its unit (e.g. "4.8 h"), as supplied by the data source.
 *
 * The icon is tinted as information (blue) rather than as a severity: the severity of the
 * reading is what the badge next to it says, and that text comes from the Rules Engine.
 */
export default function MetricCard({ icon, status, tone = "red", title, value, detail, to }) {
  const card = (
    <article className="metric">
      <div className="metric-top">
        <Icon src={icon} size={30} tone="info" />
        <StatusBadge tone={tone}>{status}</StatusBadge>
      </div>
      <p className="label">{title}</p>
      <p className="metric-value">{value}</p>
      <p className="micro">{detail}</p>
    </article>
  );
  return to ? (
    <Link to={to} className="metric-link" aria-label={`${title}: details`}>
      {card}
    </Link>
  ) : (
    card
  );
}
