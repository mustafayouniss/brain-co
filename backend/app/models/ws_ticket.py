"""WebSocket Ticket model for secure single-use multi-worker authentication.

Guarantees atomic consumption across processes and prevents JWT exposure
to client-side JavaScript. Raw ticket tokens are hashed via SHA-256 before
storage; plaintext tickets are never persisted or logged.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WebSocketTicket(Base):
    """Single-use WebSocket authorization ticket."""

    __tablename__ = "ws_tickets"

    __table_args__ = (
        Index("ix_ws_tickets_consumed_expires", "consumed", "expires_at"),
        Index("ix_ws_tickets_org_user", "organization_id", "user_id"),
    )

    ticket_hash: Mapped[str] = mapped_column(
        String(64),
        primary_key=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    case_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    consumed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    consumed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
    )
