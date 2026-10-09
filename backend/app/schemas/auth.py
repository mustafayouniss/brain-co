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
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=1, max_length=128)

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


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
