"""Pydantic schemas for multi-tenant Organization, Registration, and Membership."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.auth import UserResponse


class OrganizationRegisterRequest(BaseModel):
    """Payload for registering a new customer Organization and initial Admin user."""

    company_name: str = Field(..., min_length=2, max_length=255, description="Customer company name")
    admin_email: str = Field(..., max_length=255, description="Company administrator email")
    admin_full_name: str = Field(..., min_length=1, max_length=255, description="Administrator full name")
    password: str = Field(..., min_length=8, max_length=128, description="Administrator password")
    domain: str = Field(default="legal", max_length=50, description="Business domain extension (e.g. legal)")

    @field_validator("admin_email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address format")
        return v

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in ("legal", "sales", "hr", "logistics"):
            raise ValueError(f"Domain '{v}' is not recognized")
        return v


class OrganizationResponse(BaseModel):
    """Public organization profile."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    domain: str
    is_active: bool
    created_at: datetime


class OrganizationMembershipResponse(BaseModel):
    """Membership record binding a User to an Organization."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: str
    user_id: uuid.UUID
    role: str
    is_active: bool
    created_at: datetime


class OrganizationSignupResponse(BaseModel):
    """Response returned upon successful organization registration."""

    organization: OrganizationResponse
    user: UserResponse
    membership: OrganizationMembershipResponse
    access_token: str
    token_type: str = "bearer"


class SwitchOrganizationRequest(BaseModel):
    """Request to switch active organization context for the authenticated user."""

    organization_id: str = Field(..., min_length=1, max_length=100)


class MemberInviteRequest(BaseModel):
    """Request to create an employee account within the administrator's organization."""

    email: str = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="employee")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "employee"):
            raise ValueError("Role must be 'admin' or 'employee'")
        return v
