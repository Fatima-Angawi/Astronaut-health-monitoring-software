import StatusBadge from "./StatusBadge";
import DataSourceBadge from "./DataSourceBadge";
import { icons } from "../../data/icons";

/**
 * Headline alert block (title + severity + explanation + recommended action).
 *
 * The severity is rendered as-is: it is the verdict of the backend Rules Engine,
 * never computed here. `severitySource` labels where the verdict came from.
 */
export default function AlertCard({
  title,
  body,
  severity,
  tone = "red",
  severitySource,
  recommendationLabel,
  recommendation,
  icon = icons.warning,
}) {
  return (
    <section className="alert-card">
      <div className="alert-heading">
        <h2>{title}</h2>
        {severity && <StatusBadge tone={tone}>{severity} ALERT</StatusBadge>}
      </div>
      <p>{body}</p>
      {recommendation && (
        <div className="recommendation">
          <span>
            {recommendationLabel && <strong>{recommendationLabel} </strong>}
            {recommendation}
          </span>
          <img src={icon} alt="" />
        </div>
      )}
      {severitySource && (
        <div className="alert-source">
          <span>Severity source</span>
          <DataSourceBadge kind="engine" label={severitySource} />
        </div>
      )}
    </section>
  );
}
