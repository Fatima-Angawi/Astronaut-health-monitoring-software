import { useState } from "react";
import Icon from "../../components/common/Icon";
import StatusBadge from "../../components/common/StatusBadge";
import DataSourceBadge from "../../components/common/DataSourceBadge";
import { useToast } from "../../components/common/toastContext";
import WhyPanel from "./WhyPanel";
import { acknowledgeEpisode } from "../../api";
import { useAppState } from "../../state/context";
import { icons } from "../../data/icons";
import { iconTone, label, tone, splitIds } from "../../lib/format";

/**
 * One alert episode as the engine delivers it: its level, title, reason, action, sources
 * (Why? panel) and an acknowledge button. Nothing is evaluated here.
 *
 * The warning icon takes the colour of the engine's own level, and the toast reports the
 * outcome of the acknowledge request.
 */
export default function EpisodeCard({ episode }) {
  const { refresh } = useAppState();
  const toast = useToast();
  const [why, setWhy] = useState(false);
  const [busy, setBusy] = useState(false);
  const ids = splitIds(episode.value_ids, episode.action_value_ids);

  const acknowledge = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await acknowledgeEpisode(episode);
      toast.success(`${episode.title ?? episode.indicator_id} acknowledged.`);
      refresh();
    } catch (e) {
      toast.error(`The alert was not acknowledged: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="alert-card">
      <div className="alert-heading">
        <h2>{episode.title ?? episode.indicator_id}</h2>
        <StatusBadge tone={tone(episode.level)}>{label(episode.level).toUpperCase()} ALERT</StatusBadge>
      </div>
      <p>{episode.first_reason}</p>
      <p className="alert-reason">
        {episode.level_days} · days {episode.start_day}–{episode.end_day}
        {episode.is_standing ? " · standing alert" : ""}
        {episode.from_model ? " · from the anomaly model" : ""}
      </p>
      {episode.action && (
        <div className="recommendation">
          <span>
            <strong>Recommended: </strong>
            {episode.action}
          </span>
          <Icon src={icons.warning} size={24} tone={iconTone(episode.level)} />
        </div>
      )}
      <div className="alert-source">
        <span>Severity source</span>
        <DataSourceBadge kind="engine" label={`Rules Engine · ${episode.indicator_id}`} />
      </div>
      <div className="alert-actions">
        <button type="button" onClick={() => setWhy((v) => !v)} aria-expanded={why}>
          {why ? "Hide sources" : "Why?"}
        </button>
        <button type="button" onClick={acknowledge} disabled={busy || episode.acknowledged === 1}>
          {episode.acknowledged === 1 ? "Acknowledged" : busy ? "Sending…" : "Acknowledge"}
        </button>
      </div>
      {why && <WhyPanel ids={ids} />}
    </section>
  );
}
