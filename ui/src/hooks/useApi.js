import { useEffect, useState } from "react";
import { useAppState } from "../state/context";

/**
 * Run an api.js call and keep {data, error, loading}. Re-runs when `deps` change or when
 * the app asks for a refresh. The previous data stays on screen while a re-fetch runs.
 * Pass `enabled: false` to wait (for example until the mission day is known).
 */
export default function useApi(call, deps, enabled = true) {
  const { refreshKey } = useAppState();
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    if (!enabled) return undefined;
    let alive = true;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState((s) => ({ ...s, loading: true }));
    call()
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState({ data: null, error, loading: false }));
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, refreshKey, enabled]);

  return state;
}
