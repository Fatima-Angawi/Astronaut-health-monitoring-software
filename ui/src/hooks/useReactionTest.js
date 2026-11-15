import { useCallback, useEffect, useRef, useState } from "react";

/** Trials per test, and the wait before each stimulus (random, 1-4 s). */
export const TRIALS = 10;
const MIN_WAIT_MS = 1000;
const MAX_WAIT_MS = 4000;
/** A trial slower than this is a lapse. V018, to verify (the 10-minute PVT uses 500 ms, V014). */
export const LAPSE_MS = 355;

/** Summary of a finished run: lapses (> 355 ms), mean of the slowest 10 %, mean reaction time. */
export function summarize(times) {
  const sorted = [...times].sort((a, b) => b - a);
  const k = Math.max(1, Math.ceil(sorted.length * 0.1));
  const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
  return {
    lapses: times.filter((t) => t > LAPSE_MS).length,
    slowest10Ms: Math.round(mean(sorted.slice(0, k))),
    meanRtMs: Math.round(mean(times)),
  };
}

/**
 * Reaction-test state machine: ready -> waiting -> go -> (waiting ...) -> done.
 * Tapping during "waiting" is a false start: it is ignored and the wait restarts.
 */
export default function useReactionTest() {
  const [state, setState] = useState("ready");
  const [times, setTimes] = useState([]);
  const [falseStarts, setFalseStarts] = useState(0);
  const goAtRef = useRef(0);

  useEffect(() => {
    if (state !== "waiting") return undefined;
    const wait = MIN_WAIT_MS + Math.random() * (MAX_WAIT_MS - MIN_WAIT_MS);
    const timeout = window.setTimeout(() => {
      goAtRef.current = performance.now();
      setState("go");
    }, wait);
    return () => window.clearTimeout(timeout);
  }, [state, times.length, falseStarts]);

  const start = useCallback(() => {
    setTimes([]);
    setFalseStarts(0);
    setState("waiting");
  }, []);

  const tap = useCallback(() => {
    if (state === "waiting") {
      setFalseStarts((n) => n + 1);
      return;
    }
    if (state !== "go") return;
    const rt = Math.round(performance.now() - goAtRef.current);
    const next = [...times, rt];
    setTimes(next);
    setState(next.length >= TRIALS ? "done" : "waiting");
  }, [state, times]);

  return { state, times, falseStarts, start, tap };
}
