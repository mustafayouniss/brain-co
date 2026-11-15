"""WebSocket Connection Manager for Ring 1 Real-Time Observations & Mesh Events.

Enforces two strict authorization boundaries:
1. Boundary A (Tenant Isolation): Clients only receive events belonging to their verified organization.
2. Boundary B (Intra-Tenant Case Isolation): Case-private events are delivered ONLY to clients
   explicitly authorized and subscribed to that exact case_id.
   Unscoped (organization-level) subscribers NEVER receive case-private events.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger("app.core.ws_manager")


@dataclass(frozen=True)
class ConnectionMetadata:
    """Metadata bound to an active WebSocket connection."""
    scope_id: Optional[str]  # case_id or domain scope
    user_id: Optional[UUID]


class ObservationWebSocketManager:
    """Manages active WebSocket connections partitioned by organization_id."""

    def __init__(self) -> None:
        # organization_id -> dict[WebSocket, ConnectionMetadata]
        self._connections: dict[str, dict[WebSocket, ConnectionMetadata]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        organization_id: str,
        scope_id: Optional[str] = None,
        user_id: Optional[UUID] = None,
    ) -> None:
        """Register an authenticated WebSocket connection with verified org and scope."""
        await websocket.accept()
        org_id = organization_id.strip()
        if org_id not in self._connections:
            self._connections[org_id] = {}

        clean_scope = scope_id.strip() if scope_id and scope_id.strip() else None
        self._connections[org_id][websocket] = ConnectionMetadata(
            scope_id=clean_scope,
            user_id=user_id,
        )
        logger.info(
            "WebSocket client connected for org '%s' (user: %s, filter scope: %s). Total active in org: %d",
            org_id,
            user_id,
            clean_scope,
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

    async def disconnect_user(self, organization_id: str, user_id: UUID) -> int:
        """Forcefully disconnect all connections for a user whose access was revoked."""
        org_id = organization_id.strip()
        connections_for_org = self._connections.get(org_id, {})
        closed_count = 0
        for ws, meta in list(connections_for_org.items()):
            if meta.user_id == user_id:
                try:
                    await ws.close(code=1008)
                except Exception:
                    pass
                self.disconnect(ws, org_id)
                closed_count += 1
        return closed_count

    async def broadcast_event(
        self,
        organization_id: str,
        event_payload: dict[str, Any],
        case_id: Optional[str] = None,
    ) -> int:
        """Broadcast a structured Mesh lifecycle event under strict dual-boundary filtering.

        Boundary Rules:
        - Tenant Isolation: Only delivered to clients matching organization_id.
        - Case Isolation: If case_id is specified (case-private event), it is delivered
          ONLY to connections where meta.scope_id == case_id.
          Unscoped subscribers (meta.scope_id is None) NEVER receive case-private payloads.
        - Organization-wide events (case_id is None) are delivered only to unscoped subscribers.
        """
        org_id = organization_id.strip()
        connections_for_org = self._connections.get(org_id)
        if not connections_for_org:
            return 0

        target_case = case_id.strip() if case_id and case_id.strip() else None
        serialized = json.dumps(event_payload, default=str)

        dead_connections: list[WebSocket] = []
        sent_count = 0

        for ws, meta in list(connections_for_org.items()):
            # Boundary B Enforcement:
            if target_case:
                # Case-private event: MUST match connection's authorized case_id
                if meta.scope_id != target_case:
                    continue
            else:
                # Organization-wide event: deliver only to unscoped subscribers
                if meta.scope_id is not None:
                    continue

            try:
                await ws.send_text(serialized)
                sent_count += 1
            except Exception as e:
                logger.debug("Failed sending to WebSocket for org %s: %s; queuing for cleanup", org_id, str(e))
                dead_connections.append(ws)

        for dead_ws in dead_connections:
            self.disconnect(dead_ws, org_id)

        return sent_count

    async def broadcast_observation(
        self,
        organization_id: str,
        observation: dict[str, Any],
        scope_id: Optional[str] = None,
    ) -> int:
        """Backwards-compatible wrapper broadcasting observation.created events."""
        target_scope = (scope_id or observation.get("case_id") or observation.get("scope_id") or "").strip()
        payload = {
            "type": "observation.created",
            "data": observation,
        }
        return await self.broadcast_event(
            organization_id=organization_id,
            event_payload=payload,
            case_id=target_scope if target_scope else None,
        )

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
