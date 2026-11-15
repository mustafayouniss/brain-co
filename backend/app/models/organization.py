"""Organization & Membership models for multi-tenant SaaS architecture.

Separates Organization (customer company), Deployment (runtime environment),
and Domain (business capability extension).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Organization(Base):
    """Customer company account representing an isolated tenant."""

    __tablename__ = "organizations"

    __table_args__ = (
        Index("ix_organizations_slug", "slug", unique=True),
        Index("ix_organizations_domain", "domain"),
        Index("ix_organizations_is_active", "is_active"),
    )

    id: Mapped[str] = mapped_column(
        String(100),
        primary_key=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    domain: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="legal",
        server_default=text("'legal'"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    settings: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
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

    memberships: Mapped[list[OrganizationMembership]] = relationship(
        "OrganizationMembership",
        back_populates="organization",
        cascade="all, delete-orphan",
    )


class OrganizationMembership(Base):
    """Membership binding a User to an Organization with a verified role."""

    __tablename__ = "organization_memberships"

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'employee')",
            name="ck_membership_role",
        ),
        UniqueConstraint("organization_id", "user_id", name="uq_org_membership_user"),
        Index("ix_org_membership_org_id", "organization_id"),
        Index("ix_org_membership_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    organization_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="employee",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    organization: Mapped[Organization] = relationship(
        "Organization",
        back_populates="memberships",
    )
