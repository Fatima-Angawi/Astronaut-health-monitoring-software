import { useState } from "react";
import useReactionTest, { LAPSE_MS, summarize, TRIALS } from "../../hooks/useReactionTest";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { icons } from "../../data/icons";
import { sendPvt } from "../../api";
import { useAppState } from "../../state/context";

/**
 * Short reaction test (team design: 10 trials, not the 3-minute PVT-B). Computes pvt_lapses
 * (> 355 ms, V018 to verify), pvt_slowest10_ms and pvt_mean_rt_ms and sends them to /readings.
 * It does not score or triage: alerting is the engine's job.
 */
export default function ReactionTest() {
  const { astronautId, day, refreshSoon } = useAppState();
  const { state, times, falseStarts, start, tap } = useReactionTest();
  const [sent, setSent] = useState(null);
  const result = state === "done" ? summarize(times) : null;

  const copy = {
    ready: ["READY", `${TRIALS} trials, wait for the signal`, "Ready to start"],
    waiting: ["WAIT", "Tap only when the panel says TAP", "Get ready"],
    go: ["TAP NOW", `Trial ${times.length + 1} of ${TRIALS}`, "Go!"],
    done: [`${result?.meanRtMs ?? ""} ms`, "Mean reaction time", "Test complete"],
  }[state];

  const send = async () => {
    setSent({ text: "Sending…" });
    try {
      await sendPvt(astronautId, { ...result, missionDay: day });
      setSent({ ok: true, text: `Sent for ${astronautId}, day ${day}. Refreshing in about 10 s…` });
      refreshSoon();
    } catch (e) {
      setSent({ ok: false, text: e.message });
    }
  };

  return (
    <section className="panel reaction-card">
      <SectionHeader title="Reaction Test" action={<StatusBadge tone="blue">{TRIALS} trials</StatusBadge>} />
      <h3>Test your reaction time</h3>
      <p>Tap as quickly as possible when the panel says TAP.</p>

      <button className={`test-display ${state}`} onClick={tap} type="button">
        <img src={icons.testTimer} alt="" />
        <strong>{copy[0]}</strong>
        <span>{copy[1]}</span>
        <em>{copy[2]}</em>
      </button>

      {result && (
        <div className="pvt-result">
          <span>Lapses (&gt; {LAPSE_MS} ms): <strong>{result.lapses}</strong></span>
          <span>Slowest 10 %: <strong>{result.slowest10Ms} ms</strong></span>
          <span>Mean: <strong>{result.meanRtMs} ms</strong></span>
          {falseStarts > 0 && <span>False starts ignored: {falseStarts}</span>}
        </div>
      )}

      <button className="start-button" onClick={start} disabled={state === "waiting" || state === "go"}>
        {state === "done" ? "Run Test Again" : "Start Reaction Test"}
      </button>
      {result && (
        <button className="start-button" onClick={send} disabled={!day || sent?.ok}>
          Send result for {astronautId}
        </button>
      )}
      {sent && (
        <p className={sent.ok === false ? "async-note async-note--error" : "async-note"} role="status">
          {sent.text}
        </p>
      )}
      <p className="pvt-note">
        Lapse threshold {LAPSE_MS} ms: V018, to verify (the 10-minute PVT uses 500 ms, V014). The short
        10-trial format is a team design choice.
      </p>
    </section>
  );
}
