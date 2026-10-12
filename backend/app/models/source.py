import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Source(Base):
    """Source entity representing raw ingested data objects in Source Memory."""

    __tablename__ = "sources"

    __table_args__ = (
        CheckConstraint(
            "size_bytes > 0",
            name="ck_sources_size_bytes_positive",
        ),
        Index("ix_sources_checksum_sha256", "checksum_sha256"),
        Index("ix_sources_uploaded_by", "uploaded_by"),
        Index("ix_sources_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    original_filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    content_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    size_bytes: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    checksum_sha256: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'document'"),
    )
    storage_mode: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'local'"),
    )
    storage_key: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default=text("'ingested'"),
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
