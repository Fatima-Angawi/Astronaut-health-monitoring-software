import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";

/**
 * Flight-surgeon view of the whole crew: code, name, severity and the 7-day sleep mean
 * (hours) for each member.
 */
export default function CrewHealthSummary({ members }) {
  return (
    <Panel className="crew-summary-card">
      <SectionHeader title="Crew Health Summary" />
      <div className="crew-table" role="table" aria-label="Crew health summary">
        {members.map((member) => (
          <div className="crew-row" role="row" key={member.code}>
            <strong role="cell" className="crew-row__code">
              {member.code}
            </strong>
            <span role="cell" className="crew-row__name">
              {member.name}
            </span>
            <StatusBadge tone={member.tone}>{member.status}</StatusBadge>
            <span role="cell" className="crew-row__sleep">
              {member.sleep7dH.toFixed(1)} h
            </span>
          </div>
        ))}
      </div>
    </Panel>
  );
}
