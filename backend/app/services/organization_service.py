"""Service layer for multi-tenant Organization registration and membership management."""

from __future__ import annotations

import re
from typing import Optional
import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.services.user_service import EmailAlreadyExistsError


class OrganizationSlugConflictError(Exception):
    """Raised when an organization slug cannot be made unique."""
    pass


class OrganizationNotFoundError(Exception):
    """Raised when an organization does not exist."""
    pass


class MembershipNotFoundError(Exception):
    """Raised when a user is not a member of an organization."""
    pass


class OrganizationService:
    """Core domain service managing Organization lifecycle, memberships, and tenant routing."""

    @staticmethod
    def slugify(text: str) -> str:
        """Convert company name to URL-friendly slug."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_-]+", "-", text)
        return text.strip("-")

    @classmethod
    def register_organization(
        cls,
        session: Session,
        company_name: str,
        admin_email: str,
        admin_full_name: str,
        password: str,
        domain: str = "legal",
    ) -> tuple[Organization, User, OrganizationMembership]:
        """Atomically register a new Organization, create its Admin User, and establish Membership."""
        admin_email_norm = admin_email.strip().lower()

        # 1. Enforce unique user email
        existing_user = session.query(User).filter(func.lower(User.email) == admin_email_norm).first()
        if existing_user is not None:
            raise EmailAlreadyExistsError(f"An account with email '{admin_email_norm}' already exists")

        # 2. Generate unique slug
        base_slug = cls.slugify(company_name) or "company"
        slug = base_slug
        existing_slug = session.query(Organization).filter(Organization.slug == slug).first()
        if existing_slug is not None:
            slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"

        org_id = f"org-{uuid.uuid4().hex[:12]}"

        # 3. Create Organization entity
        organization = Organization(
            id=org_id,
            name=company_name.strip(),
            slug=slug,
            domain=domain.strip().lower(),
            is_active=True,
            settings={"default_domain": domain},
        )
        session.add(organization)
        session.flush()

        # 4. Create User entity with hashed password
        hashed = hash_password(password)
        user = User(
            email=admin_email_norm,
            full_name=admin_full_name.strip(),
            hashed_password=hashed,
            role="admin",
            is_active=True,
        )
        session.add(user)
        session.flush()

        # 5. Create OrganizationMembership entity
        membership = OrganizationMembership(
            organization_id=organization.id,
            user_id=user.id,
            role="admin",
            is_active=True,
        )
        session.add(membership)
        session.flush()

        return organization, user, membership

    @classmethod
    def get_organization(cls, session: Session, organization_id: str) -> Optional[Organization]:
        """Fetch active organization by ID."""
        return session.query(Organization).filter(
            Organization.id == organization_id,
            Organization.is_active == True,
        ).first()

    @classmethod
    def get_organization_by_slug(cls, session: Session, slug: str) -> Optional[Organization]:
        """Fetch active organization by slug."""
        return session.query(Organization).filter(
            Organization.slug == slug,
            Organization.is_active == True,
        ).first()

    @classmethod
    def list_user_organizations(
        cls, session: Session, user_id: uuid.UUID
    ) -> list[tuple[Organization, OrganizationMembership]]:
        """Retrieve all active organizations and membership roles for a user."""
        records = (
            session.query(Organization, OrganizationMembership)
            .join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id)
            .filter(
                OrganizationMembership.user_id == user_id,
                OrganizationMembership.is_active == True,
                Organization.is_active == True,
            )
            .all()
        )
        return records

    @classmethod
    def get_user_membership(
        cls, session: Session, user_id: uuid.UUID, organization_id: str
    ) -> Optional[OrganizationMembership]:
        """Verify that a user is an active member of an organization."""
        return session.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.is_active == True,
        ).first()

    @classmethod
    def add_employee_to_organization(
        cls,
        session: Session,
        admin_user_id: uuid.UUID,
        organization_id: str,
        email: str,
        full_name: str,
        password: str,
        role: str = "employee",
    ) -> tuple[User, OrganizationMembership]:
        """Add an employee to the specified organization, gated by admin membership."""
        # 1. Assert administrator authority in this organization
        admin_membership = cls.get_user_membership(session, admin_user_id, organization_id)
        if not admin_membership or admin_membership.role != "admin":
            raise PermissionError("Only organization administrators can add employees")

        email_norm = email.strip().lower()

        # 2. Check if user already exists
        user = session.query(User).filter(func.lower(User.email) == email_norm).first()
        if user is None:
            user = User(
                email=email_norm,
                full_name=full_name.strip(),
                hashed_password=hash_password(password),
                role=role,
                is_active=True,
            )
            session.add(user)
            session.flush()

        # 3. Check if membership already exists
        existing_mem = cls.get_user_membership(session, user.id, organization_id)
        if existing_mem:
            raise ValueError(f"User '{email_norm}' is already a member of organization '{organization_id}'")

        membership = OrganizationMembership(
            organization_id=organization_id,
            user_id=user.id,
            role=role,
            is_active=True,
        )
        session.add(membership)
        session.flush()

        return user, membership
