import { useAppState } from "../../state/context";
import StatusBadge from "../common/StatusBadge";

const ASTRONAUTS = ["A1", "A2", "A3", "A4"];

/**
 * Header read-outs and selectors shared by all three screens:
 * the mission day (follows /mission current_day), a day selector, and an astronaut selector.
 * `showAstronaut` is off on crew-wide screens.
 */
export default function MissionControls({ showAstronaut = true }) {
  const { mission, missionError, day, liveDay, pinned, setDay, goLive, astronautId, setAstronautId } =
    useAppState();
  const days = mission?.days ?? 180;
  const shown = day ?? "-";

  const step = (delta) => {
    const next = Math.min(days, Math.max(0, (day ?? 0) + delta));
    setDay(next);
  };

  return (
    <>
      <div>
        <span>Mission Day</span>
        <strong>
          {missionError && !mission ? "offline" : day === 0 ? "Not started" : `Day ${shown} of ${days}`}
        </strong>
        <small>
          {mission ? (mission.clock_running ? "clock running" : "clock paused") : ""}
          {pinned && liveDay !== null ? ` · live is day ${liveDay}` : ""}
        </small>
      </div>

      <div className="day-select">
        <span>Day</span>
        <div className="day-select__row">
          <button type="button" onClick={() => step(-1)} aria-label="Previous day" disabled={day === null}>
            −
          </button>
          <input
            type="number"
            min="0"
            max={days}
            value={day ?? ""}
            onChange={(e) => e.target.value !== "" && setDay(Math.min(days, Math.max(0, Number(e.target.value))))}
            aria-label="Mission day"
          />
          <button type="button" onClick={() => step(1)} aria-label="Next day" disabled={day === null}>
            +
          </button>
          <button type="button" className="day-select__live" onClick={goLive} disabled={!pinned}>
            Live
          </button>
        </div>
      </div>

      {showAstronaut && (
        <div className="day-select">
          <span>Astronaut</span>
          <select value={astronautId} onChange={(e) => setAstronautId(e.target.value)} aria-label="Astronaut">
            {ASTRONAUTS.map((id) => (
              <option key={id} value={id}>
                {id}
                {id === "A1" ? " · medical officer" : ""}
              </option>
            ))}
          </select>
        </div>
      )}

      <StatusBadge tone="neutral" title="The crew data in this demo is generated, not from real astronauts.">
        Simulated crew data
      </StatusBadge>
    </>
  );
}
