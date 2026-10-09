"""
Request-scoped dependencies for FastAPI route handlers.

Dependency hierarchy
--------------------
get_db
  └─ get_current_user   (validates Bearer token, returns active User)
       └─ require_admin (asserts role == "admin" from the DB row)

Security notes
--------------
- get_current_user raises the same generic 401 for every failure mode
  (missing header, garbage/expired/tampered token, unknown user, inactive
  user) so callers cannot fingerprint which check failed.
- require_admin reads role from the DATABASE row at call time, never from
  the token payload (D-014).
- WWW-Authenticate: Bearer is attached to every 401 raised here.
"""
import uuid
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import TokenSecurityError, decode_access_token
from app.db.session import SessionLocal
from app.models.user import User


# ---------------------------------------------------------------------------
# Database session
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session to API route handlers.

    Guarantees the session is properly closed after request processing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Auth constants
# ---------------------------------------------------------------------------

_BEARER_HEADERS = {"WWW-Authenticate": "Bearer"}

_AUTH_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers=_BEARER_HEADERS,
)

# HTTPBearer with auto_error=False so a missing header goes through our own
# uniform 401 instead of FastAPI's default plain-text 403.
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Current-user dependency
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Admin-only gate
# ---------------------------------------------------------------------------

def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Assert the authenticated user is an admin (role read from DB).

    Returns the User on success; raises 403 with a fixed generic message
    for any non-admin role.  Role is NEVER read from the token payload.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges",
        )
    return current_user
