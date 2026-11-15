import StatusBadge from "./StatusBadge";

/**
 * Marks where a value came from, so real NASA data is never confused with simulated
 * crew data or with a Rules Engine verdict.
 *
 * kind: "nasa" | "simulated" | "crew" | "engine"
 */
const SOURCES = {
  nasa: { label: "NASA", tone: "blue" },
  simulated: { label: "Simulated", tone: "neutral" },
  crew: { label: "Crew-reported", tone: "neutral" },
  engine: { label: "Rules Engine", tone: "blue" },
};

export default function DataSourceBadge({ kind = "simulated", label }) {
  const source = SOURCES[kind] ?? SOURCES.simulated;
  return <StatusBadge tone={source.tone}>{label ?? source.label}</StatusBadge>;
}
