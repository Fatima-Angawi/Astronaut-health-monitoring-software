import DetailShell from "./DetailShell";
import Async from "../../components/common/Async";
import Panel from "../../components/common/Panel";
import StatusBadge from "../../components/common/StatusBadge";
import useApi from "../../hooks/useApi";
import { getSummary } from "../../api";
import { useAppState } from "../../state/context";
import { fixed, label, roleLabel, tone } from "../../lib/format";

/** One row per astronaut: level, standing level and the latest key readings. */
export default function CrewSummaryPage({ role }) {
  const { day } = useAppState();
  const state = useApi(() => Promise.all(["A1", "A2", "A3", "A4"].map((id) => getSummary(id, day))), [day], day > 0);
  return (
    <DetailShell role={role} title="Crew Summary" showAstronaut={false} intro="Latest readings for each astronaut on the selected day. Levels come from the engine.">
      <Async state={state}>
        {(list) => (
          <Panel className="actions-card">
            {list.map((s) => (
              <div className="action-item" key={s.astronaut_id}>
                <div className="action-title">
                  <strong>
                    {s.astronaut_id} · {roleLabel(s.status.role)}
                  </strong>
                  <StatusBadge tone={tone(s.status.level)}>{label(s.status.level)}</StatusBadge>
                </div>
                <p>
                  Sleep (7-day mean) {fixed(s.cards.sleep_h_7d_mean?.value)} h · PVT lapses {fixed(s.cards.pvt_lapses?.value, 0)} · mood{" "}
                  {fixed(s.cards.mood?.value, 0)} / 5
                  {s.status.standing_level !== "none" ? ` · standing ${label(s.status.standing_level)}` : ""}
                </p>
                {s.status.top_reason && <p className="alert-reason">{s.status.top_reason}</p>}
              </div>
            ))}
          </Panel>
        )}
      </Async>
    </DetailShell>
  );
}
