"use client";

import * as React from "react";
import { getStoredToken, clearToken } from "@/lib/backend-auth";

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  role: "admin" | "employee";
  is_active: boolean;
}

interface SessionState {
  user: SessionUser | null;
  loading: boolean;
}

/**
 * Reads the current session once on mount using backend JWT token.
 * The token is stored in localStorage and included in Authorization headers.
 */
export function useSession() {
  const [state, setState] = React.useState<SessionState>({ user: null, loading: true });

  const refresh = React.useCallback(async () => {
    try {
      const token = getStoredToken();
      if (!token) {
        setState({ user: null, loading: false });
        return;
      }

      const res = await fetch("/api/auth/session", {
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
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
    clearToken();
    setState({ user: null, loading: false });
  }, []);

  return { ...state, refresh, logout };
}
