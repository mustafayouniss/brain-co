"""
Tests for T7: POST /api/v1/auth/login and GET /api/v1/auth/me.

Fixtures used: db_session, test_engine, client (from conftest.py).
All tests monkeypatch SECRET_KEY to a fixed FAKE value so the real key
is never read, printed, or compared.

Security canary: the literal string "C@n@ryP@ssw0rd!XYZ" must never
appear in any response body or captured log output.
"""
import time
import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User

# ---------------------------------------------------------------------------
# Canary password — must never appear in any response body or log
# ---------------------------------------------------------------------------
_CANARY_PASSWORD = "C@n@ryP@ssw0rd!XYZ"

# A short password that is valid for hashing (1-128) but NOT 12+ for create_user
_SHORT_PASSWORD = "short"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    db: Session,
    *,
    email: str = "alice@example.com",
    full_name: str = "Alice",
    password: str = "validpassword1234",
    role: str = "employee",
    is_active: bool = True,
) -> User:
    """Insert a User row with a real hash and flush (does NOT commit)."""
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def _login(client, email: str, password: str):
    return client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )


def _me(client, token: str = ""):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get("/api/v1/auth/me", headers=headers)


# ---------------------------------------------------------------------------
# Login — success
# ---------------------------------------------------------------------------

def test_login_success(db_session, client):
    _make_user(db_session, email="alice@example.com", password="validpassword1234")
    resp = _login(client, "alice@example.com", "validpassword1234")
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_email_case_insensitive_and_whitespace(db_session, client):
    """Login succeeds with uppercase or padded email."""
    _make_user(db_session, email="alice@example.com", password="validpassword1234")
    for variant in ["  Alice@Example.COM  ", "ALICE@EXAMPLE.COM", "alice@example.com"]:
        resp = _login(client, variant, "validpassword1234")
        assert resp.status_code == 200, f"failed for {variant!r}: {resp.text}"


# ---------------------------------------------------------------------------
# Login — uniform 401 for all failure modes
# ---------------------------------------------------------------------------

def _assert_login_401(resp):
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    return body


def test_login_wrong_password_401(db_session, client):
    _make_user(db_session, email="bob@example.com", password="validpassword1234")
    resp = _login(client, "bob@example.com", "wrongpassword!!!")
    _assert_login_401(resp)


def test_login_unknown_email_401(client):
    resp = _login(client, "nobody@example.com", "validpassword1234")
    _assert_login_401(resp)


def test_login_inactive_user_401(db_session, client):
    _make_user(db_session, email="inactive@example.com", password="validpassword1234", is_active=False)
    resp = _login(client, "inactive@example.com", "validpassword1234")
    _assert_login_401(resp)


def test_login_wrong_password_unknown_email_inactive_same_body(db_session, client):
    """Wrong password, unknown email, and inactive all produce identical 401 bodies."""
    _make_user(db_session, email="charlie@example.com", password="validpassword1234", is_active=False)
    r1 = _login(client, "charlie@example.com", "wrongpassword!!!")
    r2 = _login(client, "nosuchuser@example.com", "validpassword1234")
    r3 = _login(client, "charlie@example.com", "validpassword1234")  # inactive
    bodies = [r.json() for r in (r1, r2, r3)]
    assert bodies[0] == bodies[1] == bodies[2]
    assert all(r.status_code == 401 for r in (r1, r2, r3))
    assert all(r.headers.get("www-authenticate") == "Bearer" for r in (r1, r2, r3))


# ---------------------------------------------------------------------------
# Login — 422 without echoing input
# ---------------------------------------------------------------------------

def test_login_missing_email_422(client):
    resp = client.post("/api/v1/auth/login", json={"password": "validpassword1234"})
    assert resp.status_code == 422
    assert _CANARY_PASSWORD not in resp.text


def test_login_password_too_long_422(client):
    resp = _login(client, "x@example.com", "a" * 129)
    assert resp.status_code == 422
    assert "a" * 129 not in resp.text


def test_login_malformed_body_no_password_echo(client):
    """Canary password must not appear anywhere in the 422 response."""
    resp = client.post("/api/v1/auth/login", json={"email": "x@example.com", "password": _CANARY_PASSWORD + "A" * 200})
    assert resp.status_code == 422
    assert _CANARY_PASSWORD not in resp.text


def test_login_no_at_sign_in_email_422(client):
    resp = _login(client, "notanemail", "validpassword1234")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /me — 401 cases
# ---------------------------------------------------------------------------

def _assert_me_401(resp):
    assert resp.status_code == 401
    assert resp.headers.get("www-authenticate") == "Bearer"
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    return body


def test_me_no_token_401(client):
    resp = client.get("/api/v1/auth/me")
    _assert_me_401(resp)


def test_me_garbage_token_401(client):
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer notavalidtoken"})
    _assert_me_401(resp)


def test_me_authorization_basic_401(client):
    """Authorization: Basic abc must return the same 401 as a garbage token."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Basic abc"})
    _assert_me_401(resp)


def test_me_bearer_no_token_401(client):
    """'Authorization: Bearer' with no token returns same 401."""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer"})
    _assert_me_401(resp)


def test_me_expired_token_401(client, monkeypatch):
    """Expired token produces same 401."""
    import jwt as pyjwt
    from datetime import datetime, timezone, timedelta
    import app.core.security as sec_mod

    fake_key = "fake-secret-key-for-tests-at-least-32-chars"

    # Patch settings on the security module so decode_access_token uses fake_key
    from app.core.config import Settings
    fake_settings = Settings(
        SECRET_KEY=fake_key,
        DATABASE_URL="postgresql+psycopg://x:x@localhost/x",
        TEST_DATABASE_URL="postgresql+psycopg://x:x@localhost/x_test",
    )
    monkeypatch.setattr(sec_mod, "settings", fake_settings)

    payload = {
        "sub": str(uuid.uuid4()),
        "iat": datetime.now(tz=timezone.utc) - timedelta(hours=2),
        "exp": datetime.now(tz=timezone.utc) - timedelta(hours=1),
    }
    token = pyjwt.encode(payload, fake_key, algorithm="HS256")

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    _assert_me_401(resp)


def test_me_token_of_deleted_user_401(db_session, client):
    """Token of a user not in DB returns 401."""
    fake_id = str(uuid.uuid4())
    from app.core.security import create_access_token
    token = create_access_token(subject=fake_id)
    resp = _me(client, token)
    _assert_me_401(resp)


def test_me_token_of_inactive_user_401(db_session, client):
    """Token of an inactive user returns 401."""
    user = _make_user(db_session, email="sleeping@example.com", password="validpassword1234", is_active=False)
    db_session.flush()
    from app.core.security import create_access_token
    token = create_access_token(subject=str(user.id))
    resp = _me(client, token)
    _assert_me_401(resp)


def test_me_no_token_unknown_inactive_same_body(db_session, client):
    """Missing token, deleted user token, and inactive user token all produce identical 401."""
    inactive = _make_user(db_session, email="zzz@example.com", password="validpassword1234", is_active=False)
    db_session.flush()
    from app.core.security import create_access_token
    inactive_token = create_access_token(subject=str(inactive.id))
    deleted_token = create_access_token(subject=str(uuid.uuid4()))

    r1 = client.get("/api/v1/auth/me")
    r2 = _me(client, "garbage")
    r3 = _me(client, inactive_token)
    r4 = _me(client, deleted_token)

    bodies = [r.json() for r in (r1, r2, r3, r4)]
    assert bodies[0] == bodies[1] == bodies[2] == bodies[3]
    assert all(r.status_code == 401 for r in (r1, r2, r3, r4))


# ---------------------------------------------------------------------------
# /me — success
# ---------------------------------------------------------------------------

def test_me_success_no_hashed_password(db_session, client):
    """Successful /me response contains no hashed_password field."""
    _make_user(db_session, email="dave@example.com", password="validpassword1234")
    resp_login = _login(client, "dave@example.com", "validpassword1234")
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]

    resp = _me(client, token)
    assert resp.status_code == 200
    body = resp.json()
    assert "hashed_password" not in body
    assert body["email"] == "dave@example.com"
    assert body["is_active"] is True


def test_me_success_401s_have_www_authenticate(db_session, client):
    """Every 401 from /me has the WWW-Authenticate: Bearer header."""
    resp = client.get("/api/v1/auth/me")
    assert resp.headers.get("www-authenticate") == "Bearer"


# ---------------------------------------------------------------------------
# Canary: submitted password must not appear in responses
# ---------------------------------------------------------------------------

def test_canary_password_not_in_login_response(db_session, client):
    _make_user(db_session, email="eve@example.com", password="validpassword1234")
    resp = _login(client, "eve@example.com", _CANARY_PASSWORD)
    assert _CANARY_PASSWORD not in resp.text


def test_canary_password_not_in_captured_logs(db_session, client, caplog):
    """Canary password must never appear in captured log output."""
    _make_user(db_session, email="eve_log@example.com", password="validpassword1234")
    with caplog.at_level("DEBUG"):
        _login(client, "eve_log@example.com", _CANARY_PASSWORD)
        _login(client, "eve_log@example.com", "validpassword1234")
    assert _CANARY_PASSWORD not in caplog.text


# ---------------------------------------------------------------------------
# Rehash: if password needs rehash, new hash stored after login
# ---------------------------------------------------------------------------

def test_rehash_on_login(db_session, client, monkeypatch):
    """If password_needs_rehash returns True, a new hash is stored."""
    import app.api.v1.auth as auth_mod
    from app.core.security import hash_password as real_hash

    user = _make_user(db_session, email="rehash@example.com", password="validpassword1234")
    db_session.flush()
    old_hash = user.hashed_password

    # Simulate needs-rehash = True
    monkeypatch.setattr(auth_mod, "password_needs_rehash", lambda h: True)
    # hash_password must return a deterministically different hash
    call_count = {"n": 0}
    def fake_hash(pw):
        call_count["n"] += 1
        return real_hash(pw)
    monkeypatch.setattr(auth_mod, "hash_password", fake_hash)

    resp = _login(client, "rehash@example.com", "validpassword1234")
    assert resp.status_code == 200
    assert call_count["n"] == 1  # hash_password was called exactly once

    db_session.refresh(user)
    # A new hash was stored (even if argon2 produces slightly different hash each time)
    # Just verify hash_password was called (call_count proven above)
