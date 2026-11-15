"""WebSocket Single-Use Ticket Service for Multi-Worker Authentication.

Enforces:
1. Cryptographic randomness (256-bit URL-safe tokens).
2. Plaintext tickets are NEVER stored or logged; stored as SHA-256 hashes.
3. Atomic single-use consumption in PostgreSQL via UPDATE ... RETURNING,
   guaranteeing race-free consumption across multiple processes/workers.
4. 60-second expiration bound to user_id, organization_id, and case_id.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import secrets
from typing import Optional
import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.ws_ticket import WebSocketTicket

logger = logging.getLogger("app.services.ticket_service")

TICKET_TTL_SECONDS = 60


@dataclass(frozen=True)
class ConsumedTicket:
    """Immutable record of an atomically consumed ticket."""
    user_id: UUID
    organization_id: str
    case_id: Optional[str]
    expires_at: datetime


class TicketService:
    """Service managing the secure lifecycle of single-use WebSocket tickets."""

    @staticmethod
    def hash_ticket(raw_token: str) -> str:
        """Derive deterministic SHA-256 hash of raw ticket token."""
        return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()

    @classmethod
    def create_ticket(
        cls,
        session: Session,
        user_id: UUID,
        organization_id: str,
        case_id: Optional[str] = None,
    ) -> str:
        """Generate a cryptographically secure single-use ticket and persist its hash.

        Returns:
            The raw token string (wst_...) to be returned once to the client.
            The raw token is NEVER logged or stored in the database.
        """
        raw_token = f"wst_{secrets.token_urlsafe(32)}"
        ticket_hash = cls.hash_ticket(raw_token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=TICKET_TTL_SECONDS)

        clean_case_id = case_id.strip() if case_id and case_id.strip() else None

        ticket_record = WebSocketTicket(
            ticket_hash=ticket_hash,
            user_id=user_id,
            organization_id=organization_id.strip(),
            case_id=clean_case_id,
            created_at=now,
            expires_at=expires_at,
            consumed=False,
        )
        session.add(ticket_record)
        session.flush()

        logger.info(
            "Issued WebSocket ticket for user %s, org %s, case_scope=%s (expires in %ds)",
            user_id,
            organization_id,
            clean_case_id,
            TICKET_TTL_SECONDS,
        )
        return raw_token

    @classmethod
    def consume_ticket(
        cls,
        session: Session,
        raw_token: str,
    ) -> Optional[ConsumedTicket]:
        """Atomically consume a single-use ticket across multiple workers.

        Uses PostgreSQL's atomic UPDATE ... WHERE consumed = false AND expires_at > now()
        RETURNING ... to guarantee single-use semantics even under high concurrency.

        Returns:
            ConsumedTicket if valid and consumed successfully; None if invalid,
            already consumed (replay), or expired.
        """
        if not raw_token or not raw_token.strip():
            logger.warning("Ticket consumption rejected: empty token")
            return None

        ticket_hash = cls.hash_ticket(raw_token)
        now = datetime.now(timezone.utc)

        # Atomic update and fetch in a single database round-trip
        stmt = (
            sa.update(WebSocketTicket)
            .where(
                WebSocketTicket.ticket_hash == ticket_hash,
                WebSocketTicket.consumed.is_(False),
                WebSocketTicket.expires_at > now,
            )
            .values(
                consumed=True,
                consumed_at=now,
            )
            .returning(
                WebSocketTicket.user_id,
                WebSocketTicket.organization_id,
                WebSocketTicket.case_id,
                WebSocketTicket.expires_at,
            )
        )

        result = session.execute(stmt).fetchone()
        if not result:
            logger.warning("Ticket consumption failed: invalid, expired, or replayed")
            return None

        user_id, org_id, case_id, expires_at = result
        session.commit()

        logger.info(
            "Successfully consumed ticket for user %s, org %s, case_scope=%s",
            user_id,
            org_id,
            case_id,
        )
        return ConsumedTicket(
            user_id=user_id,
            organization_id=org_id,
            case_id=case_id,
            expires_at=expires_at,
        )
