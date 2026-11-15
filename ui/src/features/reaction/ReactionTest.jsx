import { useState } from "react";
import useReactionTest, { LAPSE_MS, summarize, TRIALS } from "../../hooks/useReactionTest";
import Icon from "../../components/common/Icon";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../components/common/toastContext";
import { icons } from "../../data/icons";
import { sendPvt, settings } from "../../api";
import { useAppState } from "../../state/context";

/**
 * Short reaction test (team design: 10 trials, not the 3-minute PVT-B). Computes pvt_lapses
 * (> 355 ms, V018 to verify), pvt_slowest10_ms and pvt_mean_rt_ms and sends them to /readings.
 * It does not score or triage: alerting is the engine's job.
 *
 * The toast reports the real outcome of that POST: success only after the API accepted the
 * readings. While the request is in flight the button is disabled, so it cannot be sent twice.
 */
export default function ReactionTest() {
  const { astronautId, day, refreshSoon } = useAppState();
  const { state, times, falseStarts, start, tap } = useReactionTest();
  const toast = useToast();
  const [busy, setBusy] = useState(false);
  const result = state === "done" ? summarize(times) : null;

  const copy = {
    ready: ["READY", `${TRIALS} trials, wait for the signal`, "Ready to start"],
    waiting: ["WAIT", "Tap only when the panel says TAP", "Get ready"],
    go: ["TAP NOW", `Trial ${times.length + 1} of ${TRIALS}`, "Go!"],
    done: [`${result?.meanRtMs ?? ""} ms`, "Mean reaction time", "Test complete"],
  }[state];

  const send = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await sendPvt(astronautId, { ...result, missionDay: day });
      // Sample mode returns without sending anything, so it must not claim the data was saved.
      if (settings.useSamples) {
        toast.info("Sample data: the reaction test was not sent to the API.");
      } else {
        toast.success("Reaction Test submitted successfully.");
      }
      refreshSoon();
    } catch (e) {
      toast.error(`Reaction Test was not submitted: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel reaction-card">
      <SectionHeader title="Reaction Test" action={<StatusBadge tone="blue">{TRIALS} trials</StatusBadge>} />
      <h3>Test your reaction time</h3>
      <p>Tap as quickly as possible when the panel says TAP.</p>

      <button className={`test-display ${state}`} onClick={tap} type="button">
        <Icon src={icons.testTimer} size={30} tone="info" />
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
        <button className="start-button" onClick={send} disabled={busy || !day}>
          {busy ? "Sending…" : `Send result for ${astronautId}`}
        </button>
      )}
      <p className="pvt-note">
        Lapse threshold {LAPSE_MS} ms: V018, to verify (the 10-minute PVT uses 500 ms, V014). The short
        10-trial format is a team design choice.
      </p>
    </section>
  );
}
