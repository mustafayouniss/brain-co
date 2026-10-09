"""
Auth endpoints: login and current-user.

Security design
---------------
- POST /auth/login returns uniform 401 (same status, body, header) for:
    unknown email, wrong password, inactive user.
  This prevents user-enumeration attacks (D-014).
- get_current_user returns uniform 401 for:
    missing token, garbage token, expired token, inactive user,
    unknown user, bad UUID in sub.
  TokenSecurityError text and PyJWT internals never reach the response.
- WWW-Authenticate: Bearer is sent on every 401 from this module.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import (
    TokenSecurityError,
    create_access_token,
    decode_access_token,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
    hash_password,
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

_AUTH_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers=_BEARER_HEADERS,
)

# HTTPBearer with auto_error=False so a missing header goes through our own
# uniform 401 instead of FastAPI's default plain-text 403.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate Bearer token and return the active User.

    Raises the same generic 401 for every failure mode so that callers
    cannot distinguish missing token from bad token from unknown user.
    """
    if credentials is None:
        raise _AUTH_401

    try:
        payload = decode_access_token(credentials.credentials)
    except TokenSecurityError:
        raise _AUTH_401

    sub = payload.get("sub", "")
    try:
        user_id = uuid.UUID(sub)
    except (ValueError, AttributeError):
        raise _AUTH_401

    user: User | None = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _AUTH_401

    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Authenticate a user and return a Bearer access token.

    Returns the same 401 for unknown email, wrong password, and inactive
    user — prevents user enumeration.
    """
    # Always look up by lower-cased email (body.email is already normalised)
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

    # Opportunistic rehash: upgrade parameters silently on login
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
