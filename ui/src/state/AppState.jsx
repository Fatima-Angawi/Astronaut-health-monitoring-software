import { useCallback, useEffect, useMemo, useState } from "react";
import { AppState } from "./context";
import { getMission } from "../api";

const POLL_MS = 15000;

/**
 * Shared screen state: which mission day and which astronaut are shown.
 *
 * - The day follows `current_day` from /mission (not latest_day_with_data), which the API
 *   polls every 15 s, so the header advances by itself while the mission clock runs.
 * - Once the user picks a day, it stays pinned until they press "Live".
 * - `refreshKey` changes whenever screens should re-fetch (after a check-in or PVT).
 */
export function AppStateProvider({ children }) {
  const [mission, setMission] = useState(null);
  const [missionError, setMissionError] = useState(null);
  const [pinnedDay, setPinnedDay] = useState(null);
  const [astronautId, setAstronautId] = useState("A2");
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let alive = true;
    const load = () =>
      getMission()
        .then((m) => alive && (setMission(m), setMissionError(null)))
        .catch((e) => alive && setMissionError(e));
    load();
    const timer = window.setInterval(load, POLL_MS);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, []);

  const refresh = useCallback(() => setRefreshKey((k) => k + 1), []);
  /** Re-fetch about 10 s from now, after the engine has re-run on new readings. */
  const refreshSoon = useCallback(() => {
    window.setTimeout(() => setRefreshKey((k) => k + 1), 10000);
  }, []);

  const liveDay = mission?.current_day ?? null;
  const day = pinnedDay ?? liveDay;

  const value = useMemo(
    () => ({
      mission, missionError, day, liveDay, pinned: pinnedDay !== null,
      setDay: setPinnedDay, goLive: () => setPinnedDay(null),
      astronautId, setAstronautId, refreshKey, refresh, refreshSoon,
    }),
    [mission, missionError, day, liveDay, pinnedDay, astronautId, refreshKey, refresh, refreshSoon],
  );
  return <AppState.Provider value={value}>{children}</AppState.Provider>;
}
