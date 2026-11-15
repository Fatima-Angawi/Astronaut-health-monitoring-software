import { useState } from "react";
import Panel from "../../components/common/Panel";
import SectionHeader from "../../components/common/SectionHeader";
import StatusBadge from "../../components/common/StatusBadge";

/**
 * Critical task near a RED crew member, with a review workflow for the medical officer.
 *
 * The "review" action only records that the officer looked at the task; it does not
 * change any severity — that stays the Rules Engine's job.
 */
export default function CriticalTask({ task }) {
  const [reviewed, setReviewed] = useState(false);

  return (
    <Panel className="tasks-panel" aria-labelledby="critical-tasks-title">
      <SectionHeader
        title="Critical Tasks"
        id="critical-tasks-title"
        action={<StatusBadge tone="yellow">Next 48 Hours</StatusBadge>}
      />

      <div className="task-meta">
        <div className="task-time">
          <strong>
            {task.title} · {task.code}
          </strong>
          <span>{task.startTime}</span>
          <small>Mission Day {task.missionDay}</small>
        </div>
        <StatusBadge tone={reviewed ? "green" : "red"}>
          {reviewed ? "Reviewed" : "Review Required"}
        </StatusBadge>
      </div>

      <p className="task-warning">
        {reviewed ? task.reviewedMessage : task.warning}
      </p>

      <button
        className="review-button"
        type="button"
        onClick={() => setReviewed((value) => !value)}
      >
        {reviewed ? "Undo Review" : `Review ${task.title} Timing`}
      </button>
    </Panel>
  );
}
