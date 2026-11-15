import { useState } from "react";
import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";
import { useToast } from "../../components/common/toastContext";
import { acknowledgeEpisode } from "../../api";
import { useAppState } from "../../state/context";
import { clock, label, tone } from "../../lib/format";

/**
 * Next critical task (from /events) for the selected crew member. When that astronaut has an
 * alert, the button acknowledges it through the API; it never changes a severity.
 * The toast reports the outcome of that request.
 */
export default function CriticalTask({ astronautId, event, episode }) {
  const { refresh } = useAppState();
  const toast = useToast();
  const [busy, setBusy] = useState(false);

  const review = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await acknowledgeEpisode(episode);
      toast.success(`Alert for ${astronautId} acknowledged.`);
      refresh();
    } catch (e) {
      toast.error(`The alert was not acknowledged: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const acknowledged = episode?.acknowledged === 1;

  return (
    <Panel className="tasks-panel" aria-labelledby="critical-tasks-title">
      <SectionHeader
        title="Critical Tasks"
        id="critical-tasks-title"
        action={event && <StatusBadge tone="yellow">in {event.days_until} day(s)</StatusBadge>}
      />
      {!event ? (
        <p className="async-note">No critical task is planned for {astronautId}.</p>
      ) : (
        <>
          <div className="task-meta">
            <div className="task-time">
              <strong>
                {event.type} · {event.astronaut_id ?? "whole crew"}
              </strong>
              <span>{clock(event.start_time)} UTC</span>
              <small>Mission Day {event.mission_day} · simulated schedule</small>
            </div>
            {episode && <StatusBadge tone={acknowledged ? "green" : tone(episode.level)}>{acknowledged ? "Reviewed" : `${label(episode.level)} · review`}</StatusBadge>}
          </div>
          {episode && (
            <>
              <p className="task-warning">
                {astronautId} is {label(episode.level).toUpperCase()}: {episode.title}.
              </p>
              <button className="review-button" type="button" onClick={review} disabled={busy || acknowledged}>
                {acknowledged ? "Acknowledged" : busy ? "Sending…" : `Acknowledge ${astronautId} alert`}
              </button>
            </>
          )}
        </>
      )}
    </Panel>
  );
}
