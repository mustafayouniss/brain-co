"""
Auth endpoints: login and current-user.

Security design
---------------
- POST /auth/login returns uniform 401 (same status, body, header) for:
    unknown email, wrong password, inactive user.
  This prevents user-enumeration attacks (D-014).
- /auth/me delegates token validation to get_current_user (in deps.py).
- WWW-Authenticate: Bearer is sent on every 401 in this module.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import (
    TokenSecurityError,
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse

router = APIRouter()

_BEARER_HEADERS = {"WWW-Authenticate": "Bearer"}

_LOGIN_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid email or password",
    headers=_BEARER_HEADERS,
)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a Bearer access token.

    Returns the same 401 for unknown email, wrong password, and inactive
    user — prevents user enumeration (D-014).
    """
    # body.email is already stripped and lowercased by LoginRequest validator
    user: User | None = db.query(User).filter(
        func.lower(User.email) == body.email
    ).first()

    if user is None:
        # Constant-time timing mitigation for unknown users
        verify_dummy_password(body.password)
        raise _LOGIN_401

    if not verify_password(body.password, user.hashed_password):
        raise _LOGIN_401

    if not user.is_active:
        raise _LOGIN_401

    # Opportunistic rehash: upgrade hash parameters silently on login
    if password_needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(body.password)
        db.add(user)
        db.commit()

    token = create_access_token(subject=str(user.id))
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the authenticated user's profile (no hashed_password)."""
    return UserResponse.model_validate(current_user)
