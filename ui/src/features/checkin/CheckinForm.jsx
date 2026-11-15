import { useState } from "react";
import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { sendCheckin } from "../../api";
import { useAppState } from "../../state/context";

/** Daily check-in -> POST /readings (mood, stress, kss, support_requested). */
export default function CheckinForm() {
  const { astronautId, day, refreshSoon } = useAppState();
  const [mood, setMood] = useState(4);
  const [stress, setStress] = useState(2);
  const [kss, setKss] = useState(4);
  const [support, setSupport] = useState(false);
  const [status, setStatus] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setStatus(null);
    try {
      await sendCheckin(astronautId, { mood, stress, kss, supportRequested: support, missionDay: day });
      setStatus({ ok: true, text: `Sent for ${astronautId}, day ${day}. Refreshing in about 10 s…` });
      refreshSoon();
    } catch (err) {
      setStatus({ ok: false, text: err.message });
    } finally {
      setBusy(false);
    }
  };

  return (
    <Panel className="actions-card">
      <SectionHeader title="Daily Check-in" action={<StatusBadge tone="blue">Self-report</StatusBadge>} />
      <form className="checkin-form" onSubmit={submit}>
        <label>
          Mood (1–5)
          <input type="number" min="1" max="5" value={mood} onChange={(e) => setMood(Number(e.target.value))} />
        </label>
        <label>
          Stress (1–5)
          <input type="number" min="1" max="5" value={stress} onChange={(e) => setStress(Number(e.target.value))} />
        </label>
        <label>
          Sleepiness, KSS (1–9)
          <input type="number" min="1" max="9" value={kss} onChange={(e) => setKss(Number(e.target.value))} />
        </label>
        <label>
          I would like support
          <input type="checkbox" checked={support} onChange={(e) => setSupport(e.target.checked)} />
        </label>
        <button type="submit" disabled={busy || !day}>
          {busy ? "Sending…" : `Send check-in for ${astronautId}`}
        </button>
        <span className="hint">Adds new readings to the mission record; the engine re-runs afterwards.</span>
        {status && (
          <p className={status.ok ? "async-note" : "async-note async-note--error"} role="status">
            {status.text}
          </p>
        )}
      </form>
    </Panel>
  );
}
