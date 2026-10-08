from datetime import datetime, timedelta, timezone

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    TokenSecurityError,
    create_access_token,
    decode_access_token,
    hash_password,
    password_needs_rehash,
    verify_dummy_password,
    verify_password,
)

FAKE_SECRET_KEY = "test-secret-key-for-unit-testing-purposes-at-least-32-chars-long"
ANOTHER_FAKE_KEY = "another-test-secret-key-different-for-unit-testing-32-chars-long"


@pytest.fixture(autouse=True)
def mock_secret_key(monkeypatch):
    """Ensure all security tests run with a deterministic fake key."""
    from app.core import config, security

    monkeypatch.setattr(config.settings, "SECRET_KEY", FAKE_SECRET_KEY)
    monkeypatch.setattr(security.settings, "SECRET_KEY", FAKE_SECRET_KEY)


# ---------------------------------------------------------------------------
# Password Hashing Tests
# ---------------------------------------------------------------------------


def test_hash_differs_from_plain():
    """Argon2 hash is not equal to plain text password."""
    plain = "fake-test-password-123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert hashed.startswith("$argon2id$")


def test_two_hashes_of_same_password_differ():
    """Argon2 unique salt generation ensures two hashes of identical passwords differ."""
    plain = "fake-test-password-123"
    hash1 = hash_password(plain)
    hash2 = hash_password(plain)
    assert hash1 != hash2


def test_hash_password_empty_raises_value_error():
    """Empty password raises ValueError."""
    with pytest.raises(ValueError, match="must not be empty"):
        hash_password("")


def test_hash_password_overlong_raises_value_error():
    """Password exceeding 128 characters raises ValueError."""
    overlong = "a" * 129
    with pytest.raises(ValueError, match="must not exceed 128 characters"):
        hash_password(overlong)


def test_verify_password_success_and_failure():
    """verify_password returns True for matching password and False for incorrect."""
    plain = "fake-test-password-123"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_verify_malformed_hash_returns_false_and_never_raises():
    """Malformed or invalid hash strings return False without raising exceptions."""
    plain = "fake-test-password-123"
    assert verify_password(plain, "not-a-valid-argon2-hash") is False
    assert verify_password(plain, "") is False
    assert verify_password(plain, "$argon2id$broken$invalid$hash") is False
    assert verify_password("", hash_password(plain)) is False


def test_verify_dummy_password_returns_false_and_never_raises():
    """verify_dummy_password always returns False and never raises."""
    assert verify_dummy_password("any-password") is False
    assert verify_dummy_password("") is False


def test_password_needs_rehash_fresh_returns_false():
    """A freshly generated password hash does not need rehashing."""
    hashed = hash_password("fake-test-password-123")
    assert password_needs_rehash(hashed) is False


# ---------------------------------------------------------------------------
# JWT Token Tests
# ---------------------------------------------------------------------------


def test_token_round_trip():
    """Encoded token can be decoded back to the original subject."""
    sub = "user-uuid-12345"
    token = create_access_token(subject=sub, expires_minutes=15)
    payload = decode_access_token(token)

    assert payload["sub"] == sub
    assert "exp" in payload
    assert "iat" in payload


def test_expired_token_refused():
    """Token with past expiration is rejected with TokenSecurityError."""
    token = create_access_token(subject="user-uuid-12345", expires_minutes=-5)
    with pytest.raises(TokenSecurityError, match="Invalid access token"):
        decode_access_token(token)


def test_token_signed_with_another_key_refused():
    """Token signed with a different key is rejected with TokenSecurityError."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-uuid-12345",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    token = jwt.encode(payload, ANOTHER_FAKE_KEY, algorithm="HS256")

    with pytest.raises(TokenSecurityError, match="Invalid access token"):
        decode_access_token(token)


def test_tampered_token_refused():
    """Tampered token payload or signature is rejected with TokenSecurityError."""
    token = create_access_token(subject="user-uuid-12345")
    parts = token.split(".")
    tampered = f"{parts[0]}.eyJhZG1pbiI6IHRydWV9.{parts[2]}"

    with pytest.raises(TokenSecurityError, match="Invalid access token"):
        decode_access_token(tampered)


def test_token_with_alg_none_refused():
    """Tokens using algorithm 'none' are rejected."""
    import base64
    import json

    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-uuid-12345",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=15)).timestamp()),
    }
    header_json = json.dumps({"typ": "JWT", "alg": "none"}).encode("utf-8")
    payload_json = json.dumps(payload).encode("utf-8")

    h_b64 = base64.urlsafe_b64encode(header_json).rstrip(b"=").decode("ascii")
    p_b64 = base64.urlsafe_b64encode(payload_json).rstrip(b"=").decode("ascii")
    token = f"{h_b64}.{p_b64}."

    with pytest.raises(TokenSecurityError):
        decode_access_token(token)


def test_token_missing_exp_refused():
    """Token without required exp claim is rejected with TokenSecurityError."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "user-uuid-12345",
        "iat": now,
    }
    token = jwt.encode(payload, FAKE_SECRET_KEY, algorithm="HS256")

    with pytest.raises(TokenSecurityError, match="Invalid access token"):
        decode_access_token(token)


def test_token_empty_subject_refused():
    """Token with empty or non-string subject raises TokenSecurityError."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": "",
        "iat": now,
        "exp": now + timedelta(minutes=15),
    }
    token = jwt.encode(payload, FAKE_SECRET_KEY, algorithm="HS256")

    with pytest.raises(TokenSecurityError, match="Token subject must be a non-empty string"):
        decode_access_token(token)


def test_token_payload_contains_strictly_sub_iat_exp():
    """Token payload contains strictly sub, iat, exp and no sensitive fields."""
    token = create_access_token(subject="user-uuid-12345")
    payload = jwt.decode(token, options={"verify_signature": False})

    assert set(payload.keys()) == {"sub", "iat", "exp"}
    assert "role" not in payload
    assert "email" not in payload
    assert "password" not in payload


# ---------------------------------------------------------------------------
# Settings Validation Tests
# ---------------------------------------------------------------------------


def test_short_secret_key_refused():
    """Settings validator rejects secret keys shorter than 32 characters."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            SECRET_KEY="short-key",
        )
    assert "SECRET_KEY must be at least 32 characters long" in str(exc_info.value)


def test_placeholder_secret_key_refused():
    """Settings validator rejects secret keys starting with 'change-this'."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            _env_file=None,  # type: ignore[call-arg]
            SECRET_KEY="change-this-placeholder-value-that-is-long-enough-32-chars",
        )
    assert "SECRET_KEY must not use placeholder value" in str(exc_info.value)
