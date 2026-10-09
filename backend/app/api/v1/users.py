"""
POST /api/v1/users — admin-only user creation endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.user_service import EmailAlreadyExistsError, create_user

router = APIRouter()


class UserCreateRequest(BaseModel):
    email: str = Field(..., max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=12, max_length=128)
    role: str = Field(...)

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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
def create_user_endpoint(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> UserResponse:
    """Create a new user account (admin only).

    Returns 201 UserResponse on success.
    Returns 409 Conflict if email already exists (any letter case).
    Invalid input returns 422 without echoing the password.
    """
    try:
        user = create_user(
            db,
            email=body.email,
            full_name=body.full_name,
            password=body.password,
            role=body.role,
        )
        db.commit()
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    return UserResponse.model_validate(user)
