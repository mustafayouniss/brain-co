from datetime import datetime, timedelta, timezone
from typing import Any

import argon2
import argon2.exceptions
import jwt

from app.core.config import settings

# Authoritative PasswordHasher instance
_hasher = argon2.PasswordHasher()

# Precomputed dummy hash for constant-time failure when email is not found
_DUMMY_HASH: str = _hasher.hash("orgbrain-timing-mitigation-dummy-password")


class TokenSecurityError(Exception):
    """Raised for any invalid, expired, tampered, or wrongly-signed JWT."""

    pass


def hash_password(plain_password: str) -> str:
    """Hash a plain text password using Argon2id.

    Raises:
        ValueError: If password is empty or exceeds 128 characters.
    """
    if not plain_password:
        raise ValueError("Password must not be empty")
    if len(plain_password) > 128:
        raise ValueError("Password must not exceed 128 characters")
    return _hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against an Argon2 hash.

    Never raises an exception on malformed or invalid hash strings.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return _hasher.verify(hashed_password, plain_password)
    except (
        argon2.exceptions.VerifyMismatchError,
        argon2.exceptions.VerificationError,
        argon2.exceptions.InvalidHashError,
        ValueError,
        TypeError,
    ):
        return False


def verify_dummy_password(plain_password: str) -> bool:
    """Verify password against a precomputed dummy hash for unknown user timing mitigation.

    Always returns False and never raises.
    """
    try:
        _hasher.verify(_DUMMY_HASH, plain_password or "dummy")
    except Exception:
        pass
    return False


def password_needs_rehash(hashed_password: str) -> bool:
    """Check if a stored hash needs to be rehashed with updated parameters."""
    try:
        return _hasher.check_needs_rehash(hashed_password)
    except Exception:
        return True


def create_access_token(
    subject: str, expires_minutes: int | None = None
) -> str:
    """Create a signed HS256 JWT containing strictly sub, iat, and exp."""
    now = datetime.now(timezone.utc)
    duration = timedelta(
        minutes=expires_minutes
        if expires_minutes is not None
        else settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": now + duration,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate an HS256 JWT access token.

    Requires exp, iat, and sub claims.

    Raises:
        TokenSecurityError: If token is expired, invalid, tampered, wrongly-signed,
            or contains an empty subject.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"require": ["exp", "iat", "sub"]},
        )
        sub = payload.get("sub")
        if not isinstance(sub, str) or not sub.strip():
            raise TokenSecurityError("Token subject must be a non-empty string")
        return payload
    except (jwt.PyJWTError, TokenSecurityError) as exc:
        raise TokenSecurityError(f"Invalid access token: {exc}") from exc
