"""
Schemas for authentication endpoints.

Design notes
------------
- LoginRequest validates email and password inline without EmailStr
  (no extra packages required; D-009).
- Submitted values (email, password) must never appear in error messages
  (docs/api/conventions.md rule 6).
- UserResponse deliberately excludes hashed_password.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)
    organization_id: Optional[str] = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    organization_id: Optional[str] = None
    domain: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    active_organization_id: Optional[str] = None
    active_organization_name: Optional[str] = None
    active_domain: Optional[str] = None
    organizations: Optional[list[dict[str, Any]]] = None


class WSTicketRequest(BaseModel):
    case_id: Optional[str] = Field(default=None, max_length=100)


class WSTicketResponse(BaseModel):
    ticket: str
    expires_in: int = 60


    model_config = {"from_attributes": True}
