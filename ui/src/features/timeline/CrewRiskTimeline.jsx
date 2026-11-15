import { useState } from "react";
import Panel from "../../components/common/Panel";
import Divider from "../../components/common/Divider";
import StatusBadge from "../../components/common/StatusBadge";
import DataQualityBadge from "../../components/common/DataQualityBadge";
import { label, tone } from "../../lib/format";

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
export default function CrewRiskTimeline({ crew, selectedCode, onSelect, episodes, day, sentThrough }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const selected = crew.find((member) => member.code === selectedCode);
  const events = [...episodes].sort((a, b) => a.start_day - b.start_day);
  const partial = typeof sentThrough === "number" && sentThrough < day;

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
          {selected.code} · {selected.name}
        </p>
      )}

      <Divider />

      <div className="timeline-heading">
        <p className="timeline-subtitle">Alert progression · up to day {day}</p>
        <DataQualityBadge
          status={partial ? "partial" : "complete"}
          label={`Data through day ${sentThrough ?? "?"}`}
          detail={partial ? `received through day ${sentThrough}, shown day ${day}` : undefined}
        />
      </div>

      <div className="timeline-list">
        {events.length === 0 && <p className="async-note">No alerts for this astronaut.</p>}
        {events.map((item) => (
          <div className="timeline-item" key={`${item.indicator_id}-${item.start_day}-${item.is_cabin}`}>
            <StatusBadge tone={tone(item.level)}>{item.start_day}</StatusBadge>
            <div>
              <strong className="timeline-item__title">
                {item.title ?? item.indicator_id} · {label(item.level)}
              </strong>
              <span className="timeline-item__detail">{item.first_reason}</span>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}
