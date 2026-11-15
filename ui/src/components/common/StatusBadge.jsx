/**
 * Shared status/severity tag.
 *
 * Replaces the three near-duplicate implementations that existed before
 * (`pill` in the astronaut dashboard, `status-pill` in the medical dashboard and
 * `badge` in the flight surgeon dashboard). `tone` is the severity colour only —
 * the *text* (RED / Yellow / Normal / ...) always comes from the backend Rules Engine.
 *
 * Valid tones: red, orange, yellow, green, blue, neutral.
 */
export default function StatusBadge({ tone = "neutral", children, className = "", title }) {
  return (
    <span className={`pill ${tone}${className ? ` ${className}` : ""}`} title={title}>
      {children}
    </span>
  );
}
