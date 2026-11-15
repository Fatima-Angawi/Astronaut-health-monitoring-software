/** Loading / error wrapper used by every screen section. Shows children once data exists. */
export default function Async({ state, children, empty }) {
  const { data, error, loading } = state;
  if (error) {
    return (
      <p className="async-note async-note--error" role="alert">
        {error.message}
      </p>
    );
  }
  if (!data) return loading ? <p className="async-note">Loading…</p> : empty ?? null;
  return children(data);
}
