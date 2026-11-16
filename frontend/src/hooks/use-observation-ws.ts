"use client";

import * as React from "react";

export interface ObservationEvent {
  id?: string;
  run_id?: string;
  sequence_number?: number;
  observation_id?: string;
  event_type: string;
  source?: string;
  source_engine?: string;
  destination_engine?: string;
  capability?: string;
  status?: string;
  duration_ms?: number;
  plan_version?: number;
  case_id?: string | null;
  organization_id?: string;
  payload?: Record<string, any>;
  details?: Record<string, any>;
  error_details?: string | null;
  timestamp?: string;
  is_persisted?: boolean;
}

export type ConnectionStatus = "connecting" | "connected" | "reconnecting" | "disconnected" | "error";

interface UseObservationWsOptions {
  token?: string | null;
  ticket?: string | null;
  caseId?: string | null;
  enabled?: boolean;
  onEvent?: (event: ObservationEvent) => void;
}

export function useObservationWs({
  token,
  ticket,
  caseId,
  enabled = true,
  onEvent,
}: UseObservationWsOptions) {
  const [status, setStatus] = React.useState<ConnectionStatus>(enabled ? "connecting" : "disconnected");
  const [events, setEvents] = React.useState<ObservationEvent[]>([]);
  const [lastEvent, setLastEvent] = React.useState<ObservationEvent | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const socketRef = React.useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);
  const lastSeqRef = React.useRef<number | undefined>(undefined);

  const onEventRef = React.useRef(onEvent);
  onEventRef.current = onEvent;

  // Incremental historical recovery
  const fetchHistoricalEvents = React.useCallback(async (sinceSeq?: number) => {
    if (!caseId) return;
    try {
      const url = new URL(`/api/cases/${caseId}/events`, window.location.origin);
      if (sinceSeq !== undefined) {
        url.searchParams.set("since_sequence", String(sinceSeq));
      }
      const res = await fetch(url.toString());
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data.events) && data.events.length > 0) {
          setEvents((prev) => {
            const seenKeys = new Set(prev.map((e) => e.id || `${e.sequence_number}-${e.event_type}`));
            const fresh = data.events.filter(
              (e: any) => !seenKeys.has(e.id || `${e.sequence_number}-${e.event_type}`)
            );
            if (fresh.length === 0) return prev;
            return [...fresh, ...prev].slice(0, 200);
          });
          const maxSeq = Math.max(...data.events.map((e: any) => e.sequence_number || 0));
          if (maxSeq > 0) {
            lastSeqRef.current = Math.max(lastSeqRef.current || 0, maxSeq);
          }
        }
      }
    } catch (err) {
      console.debug("Historical event recovery skipped:", err);
    }
  }, [caseId]);

  // Initial historical load
  React.useEffect(() => {
    if (enabled && caseId) {
      void fetchHistoricalEvents();
    }
  }, [enabled, caseId, fetchHistoricalEvents]);

  React.useEffect(() => {
    if (!enabled) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setStatus("disconnected");
      return;
    }

    let isMounted = true;
    let retryCount = 0;

    async function getTicketOrToken(): Promise<{ paramName: string; paramVal: string } | null> {
      if (ticket) return { paramName: "ticket", paramVal: ticket };
      if (token) return { paramName: "token", paramVal: token };

      try {
        const res = await fetch("/api/auth/ws-ticket", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ case_id: caseId || undefined }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.ticket) {
            return { paramName: "ticket", paramVal: data.ticket };
          }
        }
      } catch (err) {
        console.warn("Failed to obtain WebSocket ticket:", err);
      }
      return null;
    }

    async function connect() {
      if (!isMounted) return;
      setStatus(retryCount === 0 ? "connecting" : "reconnecting");

      const auth = await getTicketOrToken();
      if (!auth) {
        if (isMounted) {
          setStatus("error");
          setError("No active session ticket for WebSocket");
        }
        return;
      }

      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = process.env.NEXT_PUBLIC_WS_URL || `${wsProtocol}//${window.location.hostname}:8000/api/v1/ws`;
      const url = new URL(`${host}/observations`);
      url.searchParams.set(auth.paramName, auth.paramVal);
      if (caseId) {
        url.searchParams.set("case_id", caseId);
      }

      try {
        const ws = new WebSocket(url.toString());
        socketRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setStatus("connected");
          setError(null);
          retryCount = 0;
          // Reconnect recovery: fetch any events that occurred while disconnected
          if (lastSeqRef.current !== undefined) {
            void fetchHistoricalEvents(lastSeqRef.current);
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data: ObservationEvent = JSON.parse(event.data);
            if (data.sequence_number) {
              lastSeqRef.current = Math.max(lastSeqRef.current || 0, data.sequence_number);
            }
            setLastEvent(data);
            setEvents((prev) => {
              const key = data.id || `${data.sequence_number}-${data.event_type}`;
              if (prev.some((e) => (e.id || `${e.sequence_number}-${e.event_type}`) === key)) {
                return prev;
              }
              return [data, ...prev].slice(0, 200);
            });
            onEventRef.current?.(data);
          } catch (e) {
            console.error("Failed to parse observation event:", e);
          }
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setStatus("error");
          setError("WebSocket connection encountered an error");
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setStatus("reconnecting");
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
          retryCount++;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        };
      } catch (err) {
        if (!isMounted) return;
        setStatus("error");
        setError(err instanceof Error ? err.message : "Failed to establish WebSocket");
      }
    }

    void connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [enabled, token, ticket, caseId, fetchHistoricalEvents]);

  return {
    status,
    connectionStatus: status,
    isConnected: status === "connected",
    events,
    lastEvent,
    error,
    clearEvents: () => setEvents([]),
  };
}
