"""Case Management Service for Ring 1.

Enforces strict case and organization boundaries per D-004 and D-006.
All queries must filter by organization_id to prevent multi-tenant data leaks.
"""

from __future__ import annotations

from typing import Optional
import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Session

from app.core.audit import AuditService
from app.models.case import Case


class CaseServiceError(Exception):
    """Base exception for case service errors."""


class CaseAlreadyExistsError(CaseServiceError):
    """Raised when case_number already exists within the organization."""


class CaseNotFoundError(CaseServiceError):
    """Raised when case is not found or does not belong to the organization."""


class CaseService:
    """Service handling case creation, retrieval, and isolation."""

    @staticmethod
    def create_case(
        session: Session,
        organization_id: str,
        case_number: str,
        title: str,
        description: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> Case:
        """Create a new case within the organization with audit logging."""
        clean_number = case_number.strip()
        clean_title = title.strip()

        # Check uniqueness within the organization
        existing = (
            session.query(Case)
            .filter(
                Case.organization_id == organization_id,
                Case.case_number == clean_number,
            )
            .first()
        )
        if existing:
            raise CaseAlreadyExistsError(
                f"Case with number '{clean_number}' already exists in organization '{organization_id}'"
            )

        new_case = Case(
            id=uuid.uuid4(),
            case_number=clean_number,
            title=clean_title,
            description=description.strip() if description else None,
            organization_id=organization_id,
            status="active",
            created_by=created_by,
        )
        session.add(new_case)
        session.flush()

        AuditService.record_event(
            session=session,
            organization_id=organization_id,
            engine_name="case_service",
            action="case_created",
            case_id=str(new_case.id),
            actor_ref=str(created_by) if created_by else None,
            payload={
                "case_number": clean_number,
                "title": clean_title,
            },
        )

        return new_case

    @staticmethod
    def list_cases(
        session: Session,
        organization_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: Optional[str] = None,
    ) -> list[Case]:
        """List cases strictly scoped to the authenticated organization."""
        query = session.query(Case).filter(Case.organization_id == organization_id)
        if status_filter:
            query = query.filter(Case.status == status_filter)

        return (
            query.order_by(Case.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_case(
        session: Session,
        organization_id: str,
        case_id: UUID,
    ) -> Optional[Case]:
        """Retrieve a specific case, verifying it belongs to the authenticated organization."""
        return (
            session.query(Case)
            .filter(
                Case.id == case_id,
                Case.organization_id == organization_id,
            )
            .first()
        )
