import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Icon from "./Icon";
import { ToastContext } from "./toastContext";
import { icons } from "../../data/icons";

/**
 * Small toast system: one stacked region, auto-dismissing messages, no extra dependency.
 *
 * A toast is only ever raised from the real outcome of a request in src/api.js: the success
 * message is shown after the API accepted the readings. A refused request, an unreachable
 * API or sample mode each get their own message, so a failure is never reported as success.
 *
 * Consumers import `useToast` from ./toastContext.
 */

/** How long a toast stays on screen, and how long its exit animation takes. */
const DURATION_MS = 5000;
const EXIT_MS = 200;
/** Only the most recent messages are kept, so the stack never covers the page on a phone. */
const MAX_VISIBLE = 3;

const TONES = {
  success: { icon: icons.check, tone: "success" },
  error: { icon: icons.actionWarning, tone: "critical" },
  info: { icon: icons.info, tone: "info" },
};

function Toast({ id, tone, message, onDismiss }) {
  const [leaving, setLeaving] = useState(false);
  const { icon, tone: iconTone } = TONES[tone] ?? TONES.info;

  useEffect(() => {
    const timer = window.setTimeout(() => setLeaving(true), DURATION_MS);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!leaving) return undefined;
    const timer = window.setTimeout(() => onDismiss(id), EXIT_MS);
    return () => window.clearTimeout(timer);
  }, [leaving, id, onDismiss]);

  return (
    <div
      className={`toast toast--${tone}${leaving ? " is-leaving" : ""}`}
      role={tone === "error" ? "alert" : "status"}
    >
      <Icon src={icon} size={22} tone={iconTone} />
      <p>{message}</p>
      <button
        type="button"
        className="toast__close"
        onClick={() => setLeaving(true)}
        aria-label="Dismiss notification"
      >
        <Icon src={icons.close} size={16} tone="muted" />
      </button>
    </div>
  );
}

export function ToastProvider({ children }) {
  const [items, setItems] = useState([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id) => setItems((list) => list.filter((t) => t.id !== id)), []);

  const notify = useCallback((tone, message) => {
    if (!message) return;
    nextId.current += 1;
    const item = { id: nextId.current, tone, message };
    setItems((list) => [...list, item].slice(-MAX_VISIBLE));
  }, []);

  const api = useMemo(
    () => ({
      success: (message) => notify("success", message),
      error: (message) => notify("error", message),
      info: (message) => notify("info", message),
      dismiss,
    }),
    [notify, dismiss],
  );

  return (
    <ToastContext.Provider value={api}>
      {children}
      <div className="toast-stack">
        {items.map((item) => (
          <Toast key={item.id} {...item} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
