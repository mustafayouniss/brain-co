"""Mesh Event Record model for durable, ordered, case-isolated execution telemetry.

Guarantees full event history persistence, deterministic sequence replay,
and multi-tenant/case-level filtering across WebSocket/SSE broadcasts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
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


class MeshEventRecord(Base):
    """Immutable, append-only durable record of a Mesh execution lifecycle event."""

    __tablename__ = "mesh_events"

    __table_args__ = (
        Index("ix_mesh_events_org_case_seq", "organization_id", "case_id", "sequence_number"),
        Index("ix_mesh_events_run_seq", "run_id", "sequence_number"),
        Index("ix_mesh_events_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(
        BigInteger,
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
    source_engine: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    destination_engine: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    capability: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    plan_version: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
