"use client";

import * as React from "react";

export interface ObservationEvent {
  observation_id: string;
  event_type: string;
  source: string;
  case_id?: string | null;
  organization_id?: string;
  payload?: Record<string, any>;
  timestamp?: string;
}

interface UseObservationWsOptions {
  token?: string | null;
  caseId?: string | null;
  enabled?: boolean;
  onEvent?: (event: ObservationEvent) => void;
}

export function useObservationWs({
  token,
  caseId,
  enabled = true,
  onEvent,
}: UseObservationWsOptions) {
  const [isConnected, setIsConnected] = React.useState(false);
  const [events, setEvents] = React.useState<ObservationEvent[]>([]);
  const [lastEvent, setLastEvent] = React.useState<ObservationEvent | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const socketRef = React.useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout | null>(null);

  const onEventRef = React.useRef(onEvent);
  onEventRef.current = onEvent;

  React.useEffect(() => {
    if (!enabled || !token) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    let isMounted = true;
    let retryCount = 0;

    function connect() {
      if (!isMounted) return;

      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const host = process.env.NEXT_PUBLIC_WS_URL || `${wsProtocol}//${window.location.hostname}:8000/api/v1/ws`;
      const url = new URL(`${host}/observations`);
      url.searchParams.set("token", token || "");
      if (caseId) {
        url.searchParams.set("case_id", caseId);
      }

      try {
        const ws = new WebSocket(url.toString());
        socketRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setIsConnected(true);
          setError(null);
          retryCount = 0;
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data: ObservationEvent = JSON.parse(event.data);
            setLastEvent(data);
            setEvents((prev) => [data, ...prev].slice(0, 50));
            onEventRef.current?.(data);
          } catch (e) {
            console.error("Failed to parse observation event:", e);
          }
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setError("WebSocket connection encountered an error");
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setIsConnected(false);
          const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
          retryCount++;
          reconnectTimeoutRef.current = setTimeout(connect, delay);
        };
      } catch (err) {
        if (!isMounted) return;
        setError(err instanceof Error ? err.message : "Failed to establish WebSocket");
      }
    }

    connect();

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
  }, [token, caseId, enabled]);

  const clearEvents = React.useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  return {
    isConnected,
    events,
    lastEvent,
    error,
    clearEvents,
  };
}
