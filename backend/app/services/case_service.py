"""Case Management Service for Ring 1.

Enforces strict case and organization boundaries per D-004 and D-006.
All queries must filter by organization_id to prevent multi-tenant data leaks.
"""

from __future__ import annotations

from typing import Optional
import uuid
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError, OperationalError
from sqlalchemy.orm import Session

from app.core.audit import AuditService
from app.models.case import Case
from app.models.case_assignment import CaseAssignment


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
        user_id: Optional[UUID] = None,
        user_role: str = "admin",
    ) -> list[Case]:
        """List cases strictly scoped to the authenticated organization and role.

        Admins see all cases in the organization.
        Employees see only cases they created or are explicitly assigned to.
        """
        query = session.query(Case).filter(Case.organization_id == organization_id)
        if status_filter:
            query = query.filter(Case.status == status_filter)

        if user_role != "admin" and user_id:
            assigned_case_ids = (
                session.query(CaseAssignment.case_id)
                .filter(CaseAssignment.user_id == user_id)
                .scalar_subquery()
            )
            query = query.filter(
                (Case.created_by == user_id) | Case.id.in_(assigned_case_ids)
            )

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

    @staticmethod
    def assign_user_to_case(
        session: Session,
        organization_id: str,
        case_id: UUID,
        user_id: UUID,
        assigned_by: Optional[UUID] = None,
    ) -> CaseAssignment:
        """Assign an employee to a case within the organization."""
        case = (
            session.query(Case)
            .filter(Case.id == case_id, Case.organization_id == organization_id)
            .first()
        )
        if not case:
            raise CaseNotFoundError(f"Case '{case_id}' not found in organization '{organization_id}'")

        existing = (
            session.query(CaseAssignment)
            .filter(CaseAssignment.case_id == case_id, CaseAssignment.user_id == user_id)
            .first()
        )
        if existing:
            return existing

        assignment = CaseAssignment(
            id=uuid.uuid4(),
            case_id=case_id,
            user_id=user_id,
            assigned_by=assigned_by,
        )
        session.add(assignment)
        session.flush()
        return assignment

    @staticmethod
    def validate_case_access(
        session: Session,
        organization_id: str,
        user_id: Optional[UUID],
        user_role: str,
        case_id_or_number: str | UUID,
    ) -> Case:
        """Validate explicit case access under CACS.

        Rules:
        1. Case must belong to organization_id.
        2. Admin: Granted access across all organization cases.
        3. Employee: Granted access if created_by == user_id OR user is in case_assignments.
        4. Case status (e.g. 'open') NEVER independently grants access.
        5. Any unauthorized attempt raises CaseNotFoundError to fail closed (never reveals case exists).
        """
        query = session.query(Case).filter(Case.organization_id == organization_id)
        if isinstance(case_id_or_number, UUID):
            case = query.filter(Case.id == case_id_or_number).first()
        else:
            clean_val = str(case_id_or_number).strip()
            try:
                parsed_uuid = UUID(clean_val)
                case = query.filter((Case.id == parsed_uuid) | (Case.case_number == clean_val)).first()
            except (ValueError, AttributeError):
                case = query.filter(Case.case_number == clean_val).first()

        if not case:
            raise CaseNotFoundError(f"Case '{case_id_or_number}' not found or access denied")

        # Admin policy: full access across organization
        if user_role == "admin":
            return case

        # Employee policy: creator or explicitly assigned
        if user_id:
            if case.created_by == user_id:
                return case

            try:
                assignment = (
                    session.query(CaseAssignment)
                    .filter(
                        CaseAssignment.case_id == case.id,
                        CaseAssignment.user_id == user_id,
                    )
                    .first()
                )
                if assignment:
                    return case
            except (ProgrammingError, OperationalError):
                session.rollback()

        # Fail closed with 404 CaseNotFoundError
        raise CaseNotFoundError(f"Case '{case_id_or_number}' not found or access denied")
