import StatusBadge from "./StatusBadge";
import { icons } from "../../data/icons";

/**
 * Selectable crew member card used by the Crew Medical Officer dashboard.
 * `member.tone` mirrors the severity assigned by the backend Rules Engine.
 */
export default function CrewMemberCard({ member, selected = false, onSelect }) {
  const className = [
    "crew-card",
    `crew-card--${member.tone}`,
    selected ? "is-selected" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type="button"
      className={className}
      onClick={() => onSelect?.(member.code)}
      aria-pressed={selected}
    >
      <span className="crew-card__identity">
        <span className="avatar">
          <img src={icons.user} alt="" />
        </span>
        <span>
          <strong className="crew-card__code">{member.code}</strong>
          <span className="crew-card__name">{member.name}</span>
        </span>
      </span>
      <span className="crew-card__role">{member.role}</span>
      <StatusBadge tone={member.tone}>{member.status}</StatusBadge>
    </button>
  );
}
