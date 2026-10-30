"""Durable Task and Outbox SQLAlchemy models for Ring 1.

Implements PostgreSQL-backed task lifecycle and Transactional Outbox pattern.
PostgreSQL is the single authoritative source of truth for task states.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TaskState(str, enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD_LETTER = "DEAD_LETTER"


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    DISPATCHING = "DISPATCHING"
    DISPATCHED = "DISPATCHED"
    FAILED_DISPATCH = "FAILED_DISPATCH"


class Task(Base):
    """Authoritative task ledger in PostgreSQL.
    
    Tracks identity, state machine transitions, worker ownership,
    fencing lease generations, and retry accounting.
    """

    __tablename__ = "tasks"

    __table_args__ = (
        Index("ix_tasks_org_state", "organization_id", "state"),
        Index("ix_tasks_case_id", "case_id"),
        Index("ix_tasks_created_at", "created_at"),
        Index("ix_tasks_lease_expiry", "state", "lease_expires_at"),
        Index(
            "uq_tasks_org_idempotency",
            "organization_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[str] = mapped_column(String(255), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    task_type: Mapped[str] = mapped_column(String(100), nullable=False, default="general_ingestion")
    state: Mapped[str] = mapped_column(
        String(50), nullable=False, default=TaskState.PENDING.value, server_default=text("'PENDING'")
    )

    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Worker ownership and lease fencing
    worker_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lease_generation: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Retry accounting
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, nullable=False, default=3, server_default=text("3")
    )

    # Payloads and results
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Correlation & lineage
    correlation_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    replayed_from_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    replayed_to_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class TaskOutbox(Base):
    """Transactional Outbox table for reliable broker dispatch.
    
    Guarantees at-least-once delivery to queue broker (Redis/ARQ) without
    holding PostgreSQL transactions open during external network calls.
    """

    __tablename__ = "task_outbox"

    __table_args__ = (
        Index("ix_task_outbox_status_lease", "status", "dispatch_lease_expires_at"),
        Index("ix_task_outbox_task_id", "task_id"),
        Index("ix_task_outbox_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    queue_name: Mapped[str] = mapped_column(String(100), nullable=False, default="ring1_tasks")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default=OutboxStatus.PENDING.value, server_default=text("'PENDING'")
    )
    dispatch_generation: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default=text("0")
    )
    dispatch_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    dispatch_lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    dispatched_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
