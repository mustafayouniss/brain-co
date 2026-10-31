"""Durable Audit Event model for Ring 1.

Every important execution decision, handoff evaluation, state transition,
and failure is recorded permanently in PostgreSQL for full traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    """Immutable, append-only execution audit record."""

    __tablename__ = "audit_events"

    __table_args__ = (
        Index("ix_audit_events_task_id", "task_id"),
        Index("ix_audit_events_org_created", "organization_id", "created_at"),
        Index("ix_audit_events_engine_action", "engine_name", "action"),
        Index("ix_audit_events_case_id", "case_id"),
        Index("ix_audit_events_correlation", "correlation_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    engine_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_state: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_state: Mapped[str | None] = mapped_column(String(50), nullable=True)

    proposed_destination: Mapped[str | None] = mapped_column(String(100), nullable=True)
    accepted_or_rejected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    execution_attempt: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    lease_generation: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    error_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    payload_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
