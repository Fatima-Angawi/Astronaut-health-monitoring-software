import { createContext, useContext } from "react";

/**
 * Toast context and its hook, kept apart from the component so Toast.jsx only exports a
 * component (keeps Fast Refresh working, same split as state/context.js).
 */
export const ToastContext = createContext(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast() must be used inside <ToastProvider>");
  return ctx;
}
