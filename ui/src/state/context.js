import { createContext, useContext } from "react";

export const AppState = createContext(null);

export function useAppState() {
  return useContext(AppState);
}
