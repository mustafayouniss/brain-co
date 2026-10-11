"use client";

import * as React from "react";

export interface SessionUser {
  email: string;
  name: string;
}

interface SessionState {
  user: SessionUser | null;
  loading: boolean;
}

/**
 * Reads the current session once on mount. Rendered server-side as logged-out
 * (the navbar's default), then upgraded when a valid cookie exists.
 */
export function useSession() {
  const [state, setState] = React.useState<SessionState>({ user: null, loading: true });

  const refresh = React.useCallback(async () => {
    try {
      const res = await fetch("/api/auth/session", { cache: "no-store" });
      const data = (await res.json()) as { user: SessionUser | null };
      setState({ user: data.user, loading: false });
    } catch {
      setState({ user: null, loading: false });
    }
  }, []);

  React.useEffect(() => {
    // Async I/O on mount (fetch session) — setState happens after the await,
    // which the Compiler lint rule cannot see through.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, [refresh]);

  const logout = React.useCallback(async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    setState({ user: null, loading: false });
  }, []);

  return { ...state, refresh, logout };
}
