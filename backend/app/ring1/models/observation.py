"""SQLAlchemy models for Ring 1 observations and memory records.

These tables support the Basic Memory Engine (store/read) and Basic Retrieval
Engine (query/filter). Context isolation is enforced by requiring a context_ref
for all context-sensitive operations, with case_id as the primary isolation key.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Observation(Base):
    """Persisted observation from the Observation Engine.

    Each observation records a normalized event with its source, context,
    and trace metadata. Duplicate detection uses the idempotency_key column.
    """

    __tablename__ = "ring1_observations"

    __table_args__ = (
        Index("ix_ring1_observations_event_type", "event_type"),
        Index("ix_ring1_observations_context_ref", "context_ref"),
        Index("ix_ring1_observations_case_id", "case_id"),
        Index("ix_ring1_observations_trace_id", "trace_id"),
        Index(
            "uq_ring1_observations_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
        Index("ix_ring1_observations_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Context isolation
    context_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Payload and metadata
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Traceability
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Duplicate detection
    idempotency_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'recorded'")
    )

    # Timestamps
    event_timestamp: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class MemoryRecord(Base):
    """Generic Ring 1 memory record for the Basic Memory Engine.

    Supports storing observations, structured content, and other Ring 1
    artifacts with full context and trace metadata. Records are scoped
    by context_ref and case_id for isolation enforcement.
    """

    __tablename__ = "ring1_memory_records"

    __table_args__ = (
        Index("ix_ring1_memory_records_record_type", "record_type"),
        Index("ix_ring1_memory_records_context_ref", "context_ref"),
        Index("ix_ring1_memory_records_case_id", "case_id"),
        Index("ix_ring1_memory_records_trace_id", "trace_id"),
        Index(
            "uq_ring1_memory_records_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
        Index("ix_ring1_memory_records_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    record_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Context isolation
    context_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    case_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    organization_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Content
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)

    # Traceability
    trace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Duplicate detection
    idempotency_key: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'active'")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
        onupdate=func.now(),
    )
