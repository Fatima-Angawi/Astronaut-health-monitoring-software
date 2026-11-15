import { useState } from "react";
import Panel from "../../components/common/Panel";
import Divider from "../../components/common/Divider";
import StatusBadge from "../../components/common/StatusBadge";
import DataQualityBadge from "../../components/common/DataQualityBadge";

function ChevronDown() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path
        d="M4 6l4 4 4-4"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/**
 * Risk progression for one crew member, with the data window and its completeness shown
 * next to the list so a partial window is never read as a full record.
 */
export default function CrewRiskTimeline({ crew, selectedCode, onSelect, timeline }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const selected = crew.find((member) => member.code === selectedCode);
  const { coverage } = timeline;

  return (
    <Panel className="timeline-panel" aria-labelledby="timeline-title">
      <h2 id="timeline-title" className="section-heading__title">
        Selected Crew Member Timeline
      </h2>

      <div className="timeline-selector">
        <span className="timeline-selector__label">Selected astronaut</span>
        <div className="crew-select">
          <button
            type="button"
            className="crew-select__trigger"
            onClick={() => setMenuOpen((open) => !open)}
            aria-expanded={menuOpen}
            aria-haspopup="listbox"
          >
            {selectedCode}
            <ChevronDown />
          </button>
          {menuOpen && (
            <div className="crew-select__menu" role="listbox" aria-label="Selected astronaut">
              {crew.map((member) => (
                <button
                  type="button"
                  role="option"
                  aria-selected={selectedCode === member.code}
                  key={member.code}
                  onClick={() => {
                    onSelect(member.code);
                    setMenuOpen(false);
                  }}
                >
                  <span className="crew-select__code">{member.code}</span>
                  <span className="crew-select__name">{member.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {selected && (
        <p className="timeline-subject">
          {selected.name} · {selected.role}
        </p>
      )}

      <Divider />

      <div className="timeline-heading">
        <p className="timeline-subtitle">{timeline.subtitle}</p>
        <DataQualityBadge
          status={coverage.status}
          label={`Coverage ${coverage.label}`}
          detail={`${coverage.coveredDays}/${coverage.expectedDays} days`}
        />
      </div>

      <div className="timeline-list">
        {timeline.events.map((item) => (
          <div className="timeline-item" key={item.id}>
            <StatusBadge tone={item.tone}>{item.day}</StatusBadge>
            <div>
              <strong className="timeline-item__title">{item.title}</strong>
              <span className="timeline-item__detail">{item.detail}</span>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
