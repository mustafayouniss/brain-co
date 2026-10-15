"use client";

import * as React from "react";
import { getStoredToken, getCurrentUser } from "@/lib/backend-auth";

export interface SessionUser {
  email: string;
  name: string;
}

interface SessionState {
  user: SessionUser | null;
  loading: boolean;
}

/**
 * Reads the current session once on mount using backend JWT token.
 * Validates token with FastAPI backend /api/v1/auth/me endpoint.
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

      const user = await getCurrentUser(token);
      setState({ 
        user: { 
          email: user.email, 
          name: user.full_name 
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
    const { clearToken } = await import("@/lib/backend-auth");
    clearToken();
    setState({ user: null, loading: false });
  }, []);

  return { ...state, refresh, logout };
}
