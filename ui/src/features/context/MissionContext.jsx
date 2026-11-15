import { Link } from "react-router-dom";
import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";
import DataSourceBadge from "../../components/common/DataSourceBadge";

/**
 * Mission context strip on the astronaut dashboard.
 *
 * Each card states where its value came from (`source`), so real NASA feeds are never
 * confused with simulated crew data. The cabin CO2 value, for example, is explicitly
 * labelled "Simulated".
 */
export default function MissionContext({ items }) {
  return (
    <Panel className="context-card" aria-labelledby="mission-context-title">
      <h2 id="mission-context-title">
        Mission Context <Link to="/astronaut/environment" className="more-link">details</Link>
      </h2>
      <div className="context-grid">
        {items.map((item) => (
          <div className="context-item" key={item.id}>
            <img src={item.icon} alt="" />
            <strong>{item.title}</strong>
            <b>{item.value}</b>
            {item.alert ? (
              <StatusBadge tone="red">{item.detail}</StatusBadge>
            ) : (
              <DataSourceBadge kind={item.source} label={item.detail} />
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}
