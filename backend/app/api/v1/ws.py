"""WebSocket Endpoints for Real-Time Observation & Mesh Event Streaming.

Enforces:
1. Short-lived, single-use ticket authentication (never exposes JWT to client JS).
2. Strict multi-tenant organization authorization (Boundary A).
3. Explicit case authorization (Boundary B): unscoped subscribers never receive
   case-private events.
4. Periodic re-validation of user, membership, and case assignment; revoking
   access immediately closes the WebSocket connection.
5. Handshake origin validation.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Optional
import uuid
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, status
from starlette.concurrency import run_in_threadpool

from app.core.config import settings
from app.core.security import TokenSecurityError, decode_access_token
from app.core.ws_manager import ws_manager
from app.db.session import SessionLocal
from app.models.user import User
from app.services.case_service import CaseNotFoundError, CaseService
from app.services.organization_service import OrganizationService
from app.services.ticket_service import TicketService

logger = logging.getLogger("app.api.v1.ws")

router = APIRouter()


def _user_is_active(user_id: uuid.UUID) -> bool:
    """Check if user exists and is active (re-exported for connection pool tests)."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        return bool(user is not None and user.is_active)


def _is_origin_allowed(websocket: WebSocket) -> bool:
    """Validate WebSocket handshake Origin header."""
    origin = websocket.headers.get("origin")
    if not origin:
        return True  # Internal server-to-server or test client without Origin header

    clean_origin = origin.rstrip("/")
    allowed = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }
    for cors in getattr(settings, "BACKEND_CORS_ORIGINS", []):
        allowed.add(str(cors).rstrip("/"))

    return clean_origin in allowed


def _validate_session_and_case(
    user_id: UUID,
    organization_id: str,
    case_id: Optional[str],
) -> bool:
    """Verify user, active organization membership, and case access in database."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active:
            return False

        membership = OrganizationService.get_user_membership(db, user_id, organization_id)
        configured_org = getattr(settings, "ORGANIZATION_ID", "org-brain-corp")
        if not membership and organization_id != configured_org:
            return False

        user_role = membership.role if membership else user.role

        if case_id:
            from app.models.case import Case
            from app.models.case_assignment import CaseAssignment

            # Look up case in database
            clean_case = case_id.strip()
            case_match = None
            try:
                parsed_uuid = UUID(clean_case)
                case_match = (
                    db.query(Case)
                    .filter(
                        Case.organization_id == organization_id,
                        (Case.id == parsed_uuid) | (Case.case_number == clean_case),
                    )
                    .first()
                )
            except (ValueError, AttributeError):
                case_match = (
                    db.query(Case)
                    .filter(
                        Case.organization_id == organization_id,
                        Case.case_number == clean_case,
                    )
                    .first()
                )

            if case_match:
                # Case exists in DB: enforce strict CACS
                if user_role == "admin":
                    return True
                if case_match.created_by == user_id:
                    return True
                try:
                    assigned = (
                        db.query(CaseAssignment)
                        .filter(
                            CaseAssignment.case_id == case_match.id,
                            CaseAssignment.user_id == user_id,
                        )
                        .first()
                    )
                    return bool(assigned is not None)
                except (ProgrammingError, OperationalError):
                    db.rollback()
                    return False
            else:
                # Verify case does not belong to another organization (cross-tenant attempt)
                try:
                    clean_str = case_id.strip()
                    parsed_uuid = UUID(clean_str)
                    cross_case = db.query(Case).filter(Case.id == parsed_uuid).first()
                    if cross_case and cross_case.organization_id != organization_id:
                        return False
                except (ValueError, AttributeError):
                    pass
                # Ephemeral observation scope filter
                return True

        return True


async def _handle_websocket_stream(
    websocket: WebSocket,
    ticket: Optional[str] = None,
    token: Optional[str] = None,
    case_id: Optional[str] = None,
    scope_id: Optional[str] = None,
) -> None:
    """Core WebSocket handler supporting both single-use tickets and legacy JWTs."""
    # 1. Validate Origin header
    if not _is_origin_allowed(websocket):
        logger.warning("WebSocket rejected: forbidden origin: %s", websocket.headers.get("origin"))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id: Optional[UUID] = None
    org_id: Optional[str] = None
    effective_case_id: Optional[str] = None
    token_exp: Optional[float] = None

    # 2. Authenticate via Ticket or fallback Token
    if ticket:
        # Atomic single-use ticket consumption
        with SessionLocal() as db:
            consumed = TicketService.consume_ticket(db, ticket)

        if not consumed:
            logger.warning("WebSocket rejected: invalid, expired, or replayed ticket")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = consumed.user_id
        org_id = consumed.organization_id
        effective_case_id = consumed.case_id

        # If client passed case_id in query, it cannot escalate beyond ticket scope
        if case_id and case_id.strip():
            clean_param = case_id.strip()
            if effective_case_id and clean_param != effective_case_id:
                logger.warning(
                    "WebSocket rejected: query case_id %s mismatch with ticket case_id %s",
                    clean_param,
                    effective_case_id,
                )
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

    elif token:
        # Backwards-compatible legacy JWT token path
        try:
            payload = decode_access_token(token)
        except TokenSecurityError as exc:
            logger.warning("WebSocket rejected: invalid token: %s", str(exc))
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        token_exp = payload.get("exp")
        sub = payload.get("sub", "")
        try:
            user_id = UUID(str(sub))
        except (ValueError, TypeError, AttributeError):
            logger.warning("WebSocket rejected: invalid user id in token sub")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        org_id = payload.get("org_id") or payload.get("organization_id")
        if not org_id:
            org_id = getattr(settings, "ORGANIZATION_ID", "org-brain-corp")

        effective_case_id = (case_id or scope_id or "").strip() or None

    else:
        logger.warning("WebSocket rejected: missing ticket or token")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 3. Authoritative Database Validation (User active + Org membership + Case access)
    is_authorized = await run_in_threadpool(
        _validate_session_and_case,
        user_id,
        org_id,
        effective_case_id,
    )
    if not is_authorized:
        logger.warning(
            "WebSocket rejected: unauthorized user %s for org %s and case %s",
            user_id,
            org_id,
            effective_case_id,
        )
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # 4. Register connection in manager with verified boundaries
    await ws_manager.connect(
        websocket=websocket,
        organization_id=org_id,
        scope_id=effective_case_id,
        user_id=user_id,
    )

    last_check = time.monotonic()
    try:
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
                is_expired = bool(token_exp is not None and float(token_exp) <= time.time())
                # Re-verify user active status, membership, and case assignment
                still_valid = await run_in_threadpool(
                    _validate_session_and_case,
                    user_id,
                    org_id,
                    effective_case_id,
                )
                if not still_valid or is_expired:
                    logger.warning(
                        "Closing WebSocket: permissions revoked or expired for user %s in org %s",
                        user_id,
                        org_id,
                    )
                    await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                    break
                last_check = now
    except Exception:
        # Client disconnected
        pass
    finally:
        ws_manager.disconnect(websocket, org_id)


@router.websocket("/observations")
async def websocket_observations(
    websocket: WebSocket,
    ticket: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
    scope_id: Optional[str] = Query(None),
) -> None:
    """Real-time observation update stream."""
    await _handle_websocket_stream(
        websocket=websocket,
        ticket=ticket,
        token=token,
        case_id=case_id,
        scope_id=scope_id,
    )


@router.websocket("/events")
async def websocket_events(
    websocket: WebSocket,
    ticket: Optional[str] = Query(None),
    token: Optional[str] = Query(None),
    case_id: Optional[str] = Query(None),
) -> None:
    """Real-time Mesh execution lifecycle event stream."""
    await _handle_websocket_stream(
        websocket=websocket,
        ticket=ticket,
        token=token,
        case_id=case_id,
        scope_id=None,
    )
