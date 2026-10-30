"""WebSocket Endpoints for Real-Time Observation Streaming.

Enforces WebSocket authentication via JWT tokens and strict tenant isolation.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import TokenSecurityError, decode_access_token
from app.core.ws_manager import ws_manager
from app.db.session import SessionLocal

logger = logging.getLogger("app.api.v1.ws")

router = APIRouter()


@router.websocket("/observations")
async def websocket_observations(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    scope_id: Optional[str] = Query(None),
) -> None:
    """Real-time observation update stream.
    
    Query Parameters:
        token: Authenticated JWT bearer token.
        case_id: Optional scope filter.
        scope_id: Optional generic domain scope filter.
    """
    configured_org = getattr(settings, "ORGANIZATION_ID", "org-brain-corp")

    # 1. Validate Token (Strictly mandatory for observation WebSocket stream)
    if not token:
        logger.warning("WebSocket rejected: missing token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    else:
        try:
            payload = decode_access_token(token)
        except TokenSecurityError as exc:
            logger.warning("WebSocket rejected: invalid token: %s", str(exc))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        token_org_id = payload.get("org_id") or payload.get("organization_id") or configured_org
        if token_org_id != configured_org:
            logger.warning(
                "WebSocket rejected: org mismatch (token org %s != config org %s)",
                token_org_id,
                configured_org,
            )
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        org_id = token_org_id

    effective_scope = scope_id or case_id

    # 2. Register connection in manager
    await ws_manager.connect(
        websocket=websocket,
        organization_id=org_id,
        scope_id=effective_scope,
    )

    try:
        # Keep connection open and receive client pings/messages
        while True:
            data = await websocket.receive_text()
            # Client can optionally send a ping or subscription update
            logger.debug("Received WebSocket message from client: %s", data[:100])
    except Exception:
        # Client disconnected
        pass
    finally:
        ws_manager.disconnect(websocket, org_id)
