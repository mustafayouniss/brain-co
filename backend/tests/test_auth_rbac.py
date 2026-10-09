"""
Tests for T8: require_admin dependency.

A minimal throwaway FastAPI app is built inside this file to test the
dependency in isolation. It calls register_exception_handlers() and uses
the same get_db override as the real app, so the 401 / 403 bodies are
the real standard-envelope shapes.

No test may use the default SessionLocal or the development DATABASE_URL.
All users are created via db_session (function-scoped, rolls back after
each test).
"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.errors import register_exception_handlers
from app.core.security import create_access_token, hash_password
from app.models.user import User


# ---------------------------------------------------------------------------
# Throwaway app fixture
# ---------------------------------------------------------------------------

def _make_throwaway_app(db_session: Session) -> FastAPI:
    """Build a minimal FastAPI app with the real error handlers and get_db
    overridden to use the isolated test session."""
    app = FastAPI()
    register_exception_handlers(app)

    # Override get_db to use the test session
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    @app.get("/admin-only")
    def admin_only_route(_: User = Depends(require_admin)):
        return {"ok": True}

    return app


@pytest.fixture
def rbac_client(db_session):
    """TestClient backed by the throwaway admin-only app."""
    app = _make_throwaway_app(db_session)
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user(
    db: Session,
    *,
    email: str,
    role: str = "employee",
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        full_name="Test User",
        hashed_password=hash_password("ValidPassword123!"),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.flush()
    return user


def _bearer(user: User) -> dict:
    return {"Authorization": f"Bearer {create_access_token(subject=str(user.id))}"}


# ---------------------------------------------------------------------------
# T8 tests
# ---------------------------------------------------------------------------

def test_admin_gets_200(db_session, rbac_client):
    """An admin with a valid token gets 200 from the admin-only route."""
    admin = _make_user(db_session, email="admin@example.com", role="admin")
    resp = rbac_client.get("/admin-only", headers=_bearer(admin))
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_employee_gets_403(db_session, rbac_client):
    """An employee gets 403 Forbidden with the standard error envelope."""
    emp = _make_user(db_session, email="emp@example.com", role="employee")
    resp = rbac_client.get("/admin-only", headers=_bearer(emp))
    assert resp.status_code == 403
    body = resp.json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == "Insufficient privileges"


def test_no_token_gets_401(rbac_client):
    """No Authorization header gets 401 with the standard error envelope."""
    resp = rbac_client.get("/admin-only")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert resp.headers.get("www-authenticate") == "Bearer"


def test_inactive_admin_gets_401(db_session, rbac_client):
    """An inactive admin cannot pass get_current_user — gets 401, not 403."""
    inactive_admin = _make_user(
        db_session,
        email="inactive_admin@example.com",
        role="admin",
        is_active=False,
    )
    resp = rbac_client.get("/admin-only", headers=_bearer(inactive_admin))
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_require_admin_reads_role_from_db(db_session, rbac_client):
    """Role is read from the DB row, not the token — downgrade test.

    Create a user as admin, change role to employee in DB without
    reissuing a token, verify the next request is 403.
    """
    user = _make_user(db_session, email="downgraded@example.com", role="admin")
    token_headers = _bearer(user)

    # Downgrade role in DB (still within the same transaction that will roll back)
    user.role = "employee"
    db_session.flush()

    resp = rbac_client.get("/admin-only", headers=token_headers)
    assert resp.status_code == 403


def test_403_body_is_standard_envelope(db_session, rbac_client):
    """403 body has the standard error envelope shape."""
    emp = _make_user(db_session, email="emp2@example.com", role="employee")
    resp = rbac_client.get("/admin-only", headers=_bearer(emp))
    body = resp.json()
    assert set(body.keys()) == {"error"}
    assert set(body["error"].keys()) >= {"code", "message"}
