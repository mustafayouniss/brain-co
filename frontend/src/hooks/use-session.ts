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
 * Reads the current session once on mount using server-side session.
 * Validates session via Next.js API route /api/auth/session.
 */
export function useSession() {
  const [state, setState] = React.useState<SessionState>({ user: null, loading: true });

  const refresh = React.useCallback(async () => {
    try {
      const response = await fetch("/api/auth/session");
      if (!response.ok) {
        setState({ user: null, loading: false });
        return;
      }

      const userData = await response.json();
      setState({ 
        user: { 
          email: userData.email, 
          name: userData.full_name 
        }, 
        loading: false 
      });
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
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } catch (error) {
      console.error("Logout failed:", error);
    }
    setState({ user: null, loading: false });
  }, []);

  return { ...state, refresh, logout };
}
