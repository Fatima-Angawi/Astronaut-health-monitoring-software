/**
 * Panel heading row: a title on the left, an optional badge or action on the right.
 */
export default function SectionHeader({ title, id, action, className = "" }) {
  return (
    <div className={`section-heading ${className}`.trim()}>
      <h2 id={id}>{title}</h2>
      {action}
    </div>
  );
}
