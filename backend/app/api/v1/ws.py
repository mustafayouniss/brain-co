"""WebSocket Endpoints for Real-Time Observation Streaming.

Enforces WebSocket authentication via JWT tokens and strict tenant isolation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional
import uuid

from fastapi import APIRouter, Query, WebSocket, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.security import TokenSecurityError, decode_access_token
from app.core.ws_manager import ws_manager
from app.db.session import SessionLocal
from app.models.user import User

logger = logging.getLogger("app.api.v1.ws")

router = APIRouter()


def _user_is_active(user_id: uuid.UUID) -> bool:
    with SessionLocal() as db:
        user = db.get(User, user_id)
        return bool(user is not None and user.is_active)


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

    # 2. Validate User is Active
    sub = payload.get("sub", "")
    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError, AttributeError):
        logger.warning("WebSocket rejected: invalid user id in sub")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    active = await run_in_threadpool(_user_is_active, user_id)
    if not active:
        logger.warning("WebSocket rejected: user %s is not active", user_id)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    effective_scope = scope_id or case_id

    # 3. Register connection in manager
    await ws_manager.connect(
        websocket=websocket,
        organization_id=org_id,
        scope_id=effective_scope,
    )

    last_check = time.monotonic()
    try:
        # Keep connection open and receive client pings/messages
        while True:
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=settings.WS_RECHECK_SECONDS,
                )
                logger.debug("Received WebSocket message from client: %s", data[:100])
            except (asyncio.TimeoutError, TimeoutError):
                pass

            now = time.monotonic()
            if now - last_check >= settings.WS_RECHECK_SECONDS:
                is_active = await run_in_threadpool(_user_is_active, user_id)
                exp = payload.get("exp")
                is_expired = bool(exp is not None and float(exp) <= time.time())
                if not is_active or is_expired:
                    logger.warning(
                        "Closing WebSocket for user %s: active=%s, expired=%s",
                        user_id,
                        is_active,
                        is_expired,
                    )
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break
                last_check = now
    except Exception:
        # Client disconnected
        pass
    finally:
        ws_manager.disconnect(websocket, org_id)
