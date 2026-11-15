/**
 * A single read-out in the navbar (mission, crew count, coverage window, ...).
 * `icon` appends small inline artwork to the value (e.g. the "On Track" status dot).
 */
export default function MissionStat({ label, value, hint, icon, className = "" }) {
  return (
    <div className={`mission-stat ${className}`.trim()}>
      <span>{label}</span>
      <strong>
        {value}
        {icon && <img src={icon} alt="" />}
      </strong>
      {hint && <small>{hint}</small>}
    </div>
  );
}
