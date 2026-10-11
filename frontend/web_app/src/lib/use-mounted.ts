import * as React from "react";

/**
 * SSR-safe "mounted" flag implemented with `useSyncExternalStore`
 * (server snapshot `false`, client snapshot `true`). Replaces the
 * `useState` + `useEffect(setMounted(true))` idiom, which the React
 * Compiler lint rule (`react-hooks/set-state-in-effect`) rejects.
 */
export function useMounted(): boolean {
  return React.useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}
