"""Organization & Membership endpoints for multi-tenant SaaS workspace."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.context import BrainContext, get_brain_context
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.schemas.auth import UserResponse
from app.schemas.organization import (
    MemberInviteRequest,
    OrganizationMembershipResponse,
    OrganizationResponse,
)
from app.services.organization_service import OrganizationService

router = APIRouter()


@router.get("/me", response_model=OrganizationResponse)
def get_current_organization(
    context: BrainContext = Depends(get_brain_context),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    """Retrieve details of the active organization established by the session context."""
    org = OrganizationService.get_organization(db, context.organization_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization '{context.organization_id}' not found",
        )
    return OrganizationResponse.model_validate(org)


@router.get("/members", response_model=list[dict])
def list_organization_members(
    context: BrainContext = Depends(get_brain_context),
    db: Session = Depends(get_db),
) -> list[dict]:
    """List members belonging to the active organization."""
    memberships = (
        db.query(OrganizationMembership, User)
        .join(User, OrganizationMembership.user_id == User.id)
        .filter(
            OrganizationMembership.organization_id == context.organization_id,
            OrganizationMembership.is_active == True,
        )
        .all()
    )
    return [
        {
            "membership_id": str(m.id),
            "user_id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": m.role,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat(),
        }
        for m, u in memberships
    ]


@router.post("/members", status_code=status.HTTP_201_CREATED, response_model=dict)
def add_organization_member(
    body: MemberInviteRequest,
    context: BrainContext = Depends(get_brain_context),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Add a new employee to the active organization (administrator authority required)."""
    if context.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization administrators can add employees",
        )

    try:
        user, membership = OrganizationService.add_employee_to_organization(
            session=db,
            admin_user_id=current_user.id,
            organization_id=context.organization_id,
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            role=body.role,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except PermissionError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return {
        "membership_id": str(membership.id),
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": membership.role,
        "organization_id": context.organization_id,
    }
