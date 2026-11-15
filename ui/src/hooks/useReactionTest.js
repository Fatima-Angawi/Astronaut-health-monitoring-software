import { useCallback, useEffect, useRef, useState } from "react";

/** Time the visual stimulus waits before turning "go". */
const STIMULUS_DELAY_MS = 1400;

/**
 * PVT-style reaction test state machine: ready -> waiting -> go -> done.
 * Kept out of the component so the timing logic is testable and reusable.
 */
export default function useReactionTest() {
  const [state, setState] = useState("ready");
  const [reactionMs, setReactionMs] = useState(null);
  const goAtRef = useRef(0);

  useEffect(() => {
    if (state !== "waiting") return undefined;
    const timeout = window.setTimeout(() => {
      goAtRef.current = performance.now();
      setState("go");
    }, STIMULUS_DELAY_MS);
    return () => window.clearTimeout(timeout);
  }, [state]);

  const start = useCallback(() => {
    if (state === "go") {
      setReactionMs(Math.round(performance.now() - goAtRef.current));
      setState("done");
      return;
    }
    setReactionMs(null);
    setState("waiting");
  }, [state]);

  return { state, reactionMs, start };
}
