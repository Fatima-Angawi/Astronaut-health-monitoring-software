import useReactionTest from "../../hooks/useReactionTest";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { icons } from "../../data/icons";

/** Display copy per state, kept in one place instead of nested ternaries in the JSX. */
const STATE_COPY = {
  ready: { strong: "03:00", hint: "Estimated test duration", chip: "Ready to start" },
  waiting: { strong: "03:00", hint: "Wait for the signal…", chip: "Get ready" },
  go: { strong: "TAP NOW", hint: "Tap the panel", chip: "Go!" },
  done: { strong: null, hint: "Reaction recorded", chip: "Test complete" },
};

/**
 * PVT-B reaction test card. Purely a self-assessment tool: it records a reaction time
 * locally and does not score or triage — PVT alerting is done by the backend engine.
 */
export default function ReactionTest() {
  const { state, reactionMs, start } = useReactionTest();
  const copy = STATE_COPY[state];
  const strong = state === "done" && reactionMs ? `${reactionMs} ms` : copy.strong;

  return (
    <section className="panel reaction-card">
      <SectionHeader title="Reaction Test" action={<StatusBadge tone="blue">PVT-B · 3 MIN</StatusBadge>} />
      <h3>Test your reaction time</h3>
      <p>Tap as quickly as possible when the visual stimulus appears.</p>

      <button
        className={`test-display ${state}`}
        onClick={state === "go" ? start : undefined}
        type="button"
      >
        <img src={icons.testTimer} alt="" />
        <strong>{strong}</strong>
        <span>{copy.hint}</span>
        <em>{copy.chip}</em>
      </button>

      <button
        className="start-button"
        onClick={start}
        disabled={state === "waiting" || state === "go"}
      >
        {state === "done" ? "Run Test Again" : "Start Reaction Test"}
      </button>
    </section>
  );
}
