"""WebSocket Connection Manager for Ring 1 Real-Time Observations.

Enforces strict tenant isolation: clients only receive observation events
belonging to their verified organization, with optional scope/case filtering.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger("app.core.ws_manager")


class ObservationWebSocketManager:
    """Manages active WebSocket connections partitioned by organization_id."""

    def __init__(self) -> None:
        # organization_id -> dict[WebSocket, Optional[str]] where value is subscribed scope_id / case_id
        self._connections: dict[str, dict[WebSocket, Optional[str]]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        organization_id: str,
        scope_id: Optional[str] = None,
    ) -> None:
        """Register an authenticated WebSocket connection."""
        await websocket.accept()
        org_id = organization_id.strip()
        if org_id not in self._connections:
            self._connections[org_id] = {}
        self._connections[org_id][websocket] = scope_id.strip() if scope_id else None
        logger.info(
            "WebSocket client connected for org '%s' (filter scope: %s). Total active in org: %d",
            org_id,
            scope_id,
            len(self._connections[org_id]),
        )

    def disconnect(self, websocket: WebSocket, organization_id: str) -> None:
        """Unregister a WebSocket connection."""
        org_id = organization_id.strip()
        if org_id in self._connections:
            self._connections[org_id].pop(websocket, None)
            if not self._connections[org_id]:
                self._connections.pop(org_id, None)
        logger.info("WebSocket client disconnected for org '%s'", org_id)

    async def broadcast_observation(
        self,
        organization_id: str,
        observation: dict[str, Any],
        scope_id: Optional[str] = None,
    ) -> int:
        """Broadcast an observation to all connected clients in the specified organization.
        
        If a client subscribed with a specific scope_id, only events matching that
        scope (or general events with no scope) will be sent to them.
        
        Returns count of clients to which the message was successfully dispatched.
        """
        org_id = organization_id.strip()
        connections_for_org = self._connections.get(org_id)
        if not connections_for_org:
            return 0

        target_scope = (scope_id or observation.get("case_id") or observation.get("scope_id") or "").strip()
        event_payload = json.dumps(
            {
                "type": "observation.created",
                "data": observation,
            },
            default=str,
        )

        dead_connections: list[WebSocket] = []
        sent_count = 0

        for ws, sub_scope in list(connections_for_org.items()):
            # If client subscribed with a specific scope, only deliver matching scope
            if sub_scope and target_scope and sub_scope != target_scope:
                continue

            try:
                await ws.send_text(event_payload)
                sent_count += 1
            except Exception as e:
                logger.debug("Failed sending to WebSocket for org %s: %s; queuing for cleanup", org_id, str(e))
                dead_connections.append(ws)

        for dead_ws in dead_connections:
            self.disconnect(dead_ws, org_id)

        return sent_count

    def get_active_count(self, organization_id: Optional[str] = None) -> int:
        """Return number of active connections."""
        if organization_id:
            return len(self._connections.get(organization_id.strip(), {}))
        return sum(len(conns) for conns in self._connections.values())

    def reset(self) -> None:
        """Clear all connections (testing utility)."""
        self._connections.clear()


# Global WebSocket manager singleton
ws_manager = ObservationWebSocketManager()
