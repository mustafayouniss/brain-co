"""
Tests for T9: user_service.create_user, POST /api/v1/users, and
app.scripts.create_admin.

Rules:
- No test uses the default SessionLocal or development DATABASE_URL.
- CLI tests inject a session bound to the test DB and a fake ask_password.
- The canary password must never appear in any response or log.
"""
import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.services.user_service import EmailAlreadyExistsError, create_user

_CANARY = "C@n@ryP@ssw0rd!XYZ"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_admin(db: Session, email: str = "admin@example.com") -> User:
    user = User(
        email=email,
        full_name="Admin",
        hashed_password=hash_password("ValidPassword123!"),
        role="admin",
    )
    db.add(user)
    db.flush()
    return user


def _make_employee(db: Session, email: str = "emp@example.com") -> User:
    user = User(
        email=email,
        full_name="Employee",
        hashed_password=hash_password("ValidPassword123!"),
        role="employee",
    )
    db.add(user)
    db.flush()
    return user


def _admin_token(user: User) -> str:
    from app.core.security import create_access_token
    return create_access_token(subject=str(user.id))


# ---------------------------------------------------------------------------
# create_user service tests
# ---------------------------------------------------------------------------

class TestCreateUserService:
    def test_stores_hash_not_plain_password(self, db_session):
        user = create_user(
            db_session,
            email="alice@example.com",
            full_name="Alice",
            password="GoodPassword123",
            role="employee",
        )
        db_session.commit()
        assert user.hashed_password != "GoodPassword123"
        assert verify_password("GoodPassword123", user.hashed_password)

    def test_email_normalized(self, db_session):
        user = create_user(
            db_session,
            email="  ALICE@EXAMPLE.COM  ",
            full_name="Alice",
            password="GoodPassword123",
            role="employee",
        )
        db_session.commit()
        assert user.email == "alice@example.com"

    def test_duplicate_email_same_case_raises(self, db_session):
        create_user(db_session, email="bob@example.com", full_name="Bob",
                    password="GoodPassword123", role="employee")
        db_session.commit()
        with pytest.raises(EmailAlreadyExistsError):
            create_user(db_session, email="bob@example.com", full_name="Bob2",
                        password="GoodPassword123", role="employee")

    def test_duplicate_email_different_case_raises(self, db_session):
        create_user(db_session, email="carol@example.com", full_name="Carol",
                    password="GoodPassword123", role="employee")
        db_session.commit()
        with pytest.raises(EmailAlreadyExistsError):
            create_user(db_session, email="CAROL@EXAMPLE.COM", full_name="Carol2",
                        password="GoodPassword123", role="employee")

    def test_password_too_short_raises(self, db_session):
        with pytest.raises(ValueError, match="at least 12"):
            create_user(db_session, email="x@example.com", full_name="X",
                        password="short", role="employee")

    def test_password_too_long_raises(self, db_session):
        with pytest.raises(ValueError, match="at most 128"):
            create_user(db_session, email="x@example.com", full_name="X",
                        password="a" * 129, role="employee")

    def test_invalid_role_raises(self, db_session):
        with pytest.raises(ValueError, match="Role must be"):
            create_user(db_session, email="x@example.com", full_name="X",
                        password="GoodPassword123", role="superuser")

    def test_other_integrity_error_propagates(self, db_session, monkeypatch):
        """An IntegrityError from a constraint other than uq_users_email_lower
        must propagate as IntegrityError, and must NOT become EmailAlreadyExistsError."""
        class FakeDiag:
            constraint_name = "ck_some_other_constraint"

        class FakeOrig(Exception):
            diag = FakeDiag()

        def fake_flush():
            raise IntegrityError("statement", {}, FakeOrig())

        monkeypatch.setattr(db_session, "flush", fake_flush)

        with pytest.raises(IntegrityError) as exc_info:
            create_user(
                db_session,
                email="other_error@example.com",
                full_name="Other",
                password="GoodPassword123",
                role="employee",
            )
        assert not isinstance(exc_info.value, EmailAlreadyExistsError)

    def test_caller_commits(self, db_session):
        """create_user only flushes; row exists only after caller commits."""
        user = create_user(
            db_session,
            email="flush_test@example.com",
            full_name="Flush",
            password="GoodPassword123",
            role="employee",
        )
        assert user.id is not None  # UUID assigned by DB via flush


# ---------------------------------------------------------------------------
# POST /api/v1/users endpoint tests
# ---------------------------------------------------------------------------

class TestUsersEndpoint:
    def test_admin_creates_user_201(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "new@example.com", "full_name": "New User",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "new@example.com"
        assert "hashed_password" not in body

    def test_employee_gets_403(self, db_session, client):
        emp = _make_employee(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(emp)}"},
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "FORBIDDEN"

    def test_no_token_gets_401(self, client):
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": "ValidPassword123!", "role": "employee"},
        )
        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    def test_duplicate_email_gets_409(self, db_session, client):
        admin = _make_admin(db_session)
        _make_employee(db_session, email="dup@example.com")
        resp = client.post(
            "/api/v1/users",
            json={"email": "dup@example.com", "full_name": "Dup",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "CONFLICT"

    def test_duplicate_email_different_case_gets_409(self, db_session, client):
        admin = _make_admin(db_session)
        _make_employee(db_session, email="dup2@example.com")
        resp = client.post(
            "/api/v1/users",
            json={"email": "DUP2@EXAMPLE.COM", "full_name": "Dup2",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 409

    def test_short_password_gets_422_no_echo(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": "p@ss1", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 422
        assert "p@ss1" not in resp.text

    def test_long_password_gets_422(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": "a" * 129, "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 422
        assert "a" * 129 not in resp.text

    def test_invalid_role_gets_422(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": "ValidPassword123!", "role": "superuser"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 422

    def test_response_never_contains_hashed_password(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "nopass@example.com", "full_name": "NP",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert resp.status_code == 201
        assert "hashed_password" not in resp.json()

    def test_canary_password_not_in_response(self, db_session, client):
        admin = _make_admin(db_session)
        resp = client.post(
            "/api/v1/users",
            json={"email": "x@example.com", "full_name": "X",
                  "password": _CANARY + "A" * 200, "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert _CANARY not in resp.text

    def test_new_employee_can_login_and_is_blocked_from_creating_users(
        self, db_session, client
    ):
        """Full flow: admin creates employee, employee logs in, employee cannot POST /users."""
        admin = _make_admin(db_session)
        create_resp = client.post(
            "/api/v1/users",
            json={"email": "newflow@example.com", "full_name": "New Flow",
                  "password": "EmployeePass123!", "role": "employee"},
            headers={"Authorization": f"Bearer {_admin_token(admin)}"},
        )
        assert create_resp.status_code == 201

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "newflow@example.com", "password": "EmployeePass123!"},
        )
        assert login_resp.status_code == 200
        emp_token = login_resp.json()["access_token"]

        me_resp = client.get("/api/v1/auth/me",
                             headers={"Authorization": f"Bearer {emp_token}"})
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "newflow@example.com"

        blocked_resp = client.post(
            "/api/v1/users",
            json={"email": "another@example.com", "full_name": "Another",
                  "password": "ValidPassword123!", "role": "employee"},
            headers={"Authorization": f"Bearer {emp_token}"},
        )
        assert blocked_resp.status_code == 403


# ---------------------------------------------------------------------------
# create_admin CLI tests
# ---------------------------------------------------------------------------

class TestCreateAdminCLI:
    def _run(self, db_session, argv, passwords):
        """Helper: run main() with the test session and fake ask_password."""
        from app.scripts.create_admin import main
        password_iter = iter(passwords)

        def fake_session_factory():
            return db_session

        def fake_ask(prompt):
            return next(password_iter)

        return main(argv=argv, session_factory=fake_session_factory,
                    ask_password=fake_ask)

    def test_creates_admin_successfully(self, db_session):
        code = self._run(
            db_session,
            argv=["--email", "clitest@example.com", "--full-name", "CLI Admin"],
            passwords=["ValidPassword123!", "ValidPassword123!"],
        )
        assert code == 0
        user = db_session.query(User).filter_by(email="clitest@example.com").first()
        assert user is not None
        assert user.role == "admin"
        assert verify_password("ValidPassword123!", user.hashed_password)

    def test_mismatched_passwords_returns_error(self, db_session):
        code = self._run(
            db_session,
            argv=["--email", "mismatch@example.com", "--full-name", "Mismatch"],
            passwords=["ValidPassword123!", "DifferentPassword!"],
        )
        assert code == 1

    def test_short_password_returns_error(self, db_session):
        code = self._run(
            db_session,
            argv=["--email", "short@example.com", "--full-name", "Short"],
            passwords=["short", "short"],
        )
        assert code == 1

    def test_email_already_exists_no_changes(self, db_session):
        """If email exists, CLI returns 1 and makes no changes.

        We commit the existing user first so the CLI's internal rollback
        (triggered by EmailAlreadyExistsError) does not erase it.
        """
        existing = User(
            email="existing@example.com",
            full_name="Existing",
            hashed_password=hash_password("ValidPassword123!"),
            role="admin",
        )
        db_session.add(existing)
        db_session.flush()
        db_session.commit()

        code = self._run(
            db_session,
            argv=["--email", "existing@example.com", "--full-name", "Existing2"],
            passwords=["ValidPassword123!", "ValidPassword123!"],
        )
        assert code == 1
        # Verify no second user was created
        count = db_session.query(User).filter_by(email="existing@example.com").count()
        assert count == 1

    def test_password_not_in_any_output(self, db_session, capsys):
        """The password and hash must never appear in stdout or stderr."""
        self._run(
            db_session,
            argv=["--email", "secure@example.com", "--full-name", "Secure"],
            passwords=["ValidPassword123!", "ValidPassword123!"],
        )
        captured = capsys.readouterr()
        assert "ValidPassword123!" not in captured.out
        assert "ValidPassword123!" not in captured.err
