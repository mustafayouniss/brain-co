"""
User creation service.

Design decisions (D-014)
-------------------------
- Password policy: 12 to 128 characters (no composition rules).
- Email is normalized (stripped, lowercased) before insertion.
- Role must be "admin" or "employee"; invalid roles raise ValueError.
- On IntegrityError we roll back and raise EmailAlreadyExistsError ONLY
  when the violated constraint is uq_users_email_lower.  Any other
  IntegrityError propagates unchanged so the caller can handle it.
- The caller is responsible for committing; create_user only flushes.
  This lets the service be composed inside a larger transaction.
"""
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User

_VALID_ROLES = frozenset({"admin", "employee"})
_EMAIL_INDEX = "uq_users_email_lower"


class EmailAlreadyExistsError(Exception):
    """Raised when an email violates the uq_users_email_lower constraint."""


def create_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    password: str,
    role: str,
) -> User:
    """Create and flush a new User.

    Validates role and password length first, then hashes and inserts.
    Does NOT commit — the caller commits.

    Raises
    ------
    ValueError
        If role is not "admin" or "employee", or if password is not
        12–128 characters long.
    EmailAlreadyExistsError
        If the email already exists (uq_users_email_lower constraint).
    IntegrityError
        Re-raised as-is for any other integrity violation.
    """
    if role not in _VALID_ROLES:
        raise ValueError(f"Role must be one of {sorted(_VALID_ROLES)}")

    length = len(password)
    if length < 12:
        raise ValueError("Password must be at least 12 characters")
    if length > 128:
        raise ValueError("Password must be at most 128 characters")

    user = User(
        email=email,            # ORM @validates normalizes this
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(user)

    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        # Only swallow the known email-uniqueness constraint
        constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint == _EMAIL_INDEX:
            raise EmailAlreadyExistsError(
                "An account with this email already exists"
            ) from exc
        raise   # propagate all other IntegrityErrors unchanged

    return user
