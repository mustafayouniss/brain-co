"""Regression tests for WebSocket database connection pool lifecycle.

Verifies that F-010 user active-status validation and periodic rechecks
do NOT leak or retain database connections from SQLAlchemy's QueuePool
during long-lived WebSocket connections.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User


@pytest.fixture
def clean_test_users(test_engine) -> Generator[list[User], None, None]:
    """Creates committed users in the test database for real-pool testing."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    users: list[User] = []
    
    with TestSession() as session:
        for i in range(5):
            u = User(
                email=f"ws_pool_user_{i}_{uuid.uuid4().hex[:6]}@example.com",
                full_name=f"Pool Test User {i}",
                hashed_password=hash_password("securepassword123"),
                role="employee",
                is_active=True,
            )
            session.add(u)
            users.append(u)
        session.commit()
        # Refresh to get persistent IDs
        for u in users:
            session.refresh(u)

    yield users

    # Cleanup
    with TestSession() as session:
        user_ids = [u.id for u in users]
        session.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
        session.commit()


def test_concurrent_websockets_release_pool_connections(test_engine, clean_test_users, monkeypatch):
    """Scenario 1 & 2: Multiple concurrent WebSockets remain open with 0 pool connections held while idle."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("app.api.v1.ws.SessionLocal", TestSession)

    checkout_events = []
    checkin_events = []

    def on_checkout(dbapi_conn, record, proxy):
        checkout_events.append(time.monotonic())

    def on_checkin(dbapi_conn, record):
        checkin_events.append(time.monotonic())

    event.listen(test_engine, "checkout", on_checkout)
    event.listen(test_engine, "checkin", on_checkin)

    open_sockets = []
    client = TestClient(app, raise_server_exceptions=False)

    try:
        # Connect 5 concurrent WebSockets
        for user in clean_test_users:
            token = create_access_token(str(user.id))
            cm = client.websocket_connect(f"/api/v1/ws/observations?token={token}")
            ws = cm.__enter__()
            open_sockets.append((cm, ws))

        # Assert: All 5 connections are actively open
        assert len(open_sockets) == 5

        # Assert: Exactly 5 checkouts occurred (1 per handshake user check)
        assert len(checkout_events) == 5

        # Assert: Exactly 5 checkins occurred (sessions immediately closed after check)
        assert len(checkin_events) == 5

        # Assert: The real connection pool has ZERO checked-out connections while WebSockets are idle
        assert test_engine.pool.checkedout() == 0

    finally:
        for cm, ws in open_sockets:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass
        event.remove(test_engine, "checkout", on_checkout)
        event.remove(test_engine, "checkin", on_checkin)


def test_http_request_succeeds_while_websockets_are_open(test_engine, clean_test_users, monkeypatch):
    """Scenario 3: Normal HTTP database request succeeds without starvation while WebSockets are connected."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("app.api.v1.ws.SessionLocal", TestSession)

    open_sockets = []
    client = TestClient(app, raise_server_exceptions=False)

    try:
        # Keep 5 WebSockets open
        for user in clean_test_users:
            token = create_access_token(str(user.id))
            cm = client.websocket_connect(f"/api/v1/ws/observations?token={token}")
            ws = cm.__enter__()
            open_sockets.append((cm, ws))

        # Assert zero connections held by open WebSockets
        assert test_engine.pool.checkedout() == 0

        # Normal HTTP request to database health endpoint (uses get_db)
        resp = client.get("/api/v1/health/db")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

        # Pool returns to 0
        assert test_engine.pool.checkedout() == 0

    finally:
        for cm, ws in open_sockets:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                pass


def test_user_deactivation_closes_websocket(test_engine, clean_test_users, monkeypatch):
    """Scenario 4: User deactivation during an active socket triggers periodic recheck closure (F-010)."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("app.api.v1.ws.SessionLocal", TestSession)
    # Accelerate recheck for deterministic testing without long sleeps
    monkeypatch.setattr(settings, "WS_RECHECK_SECONDS", 0.05)

    user = clean_test_users[0]
    token = create_access_token(str(user.id))
    client = TestClient(app, raise_server_exceptions=False)

    with client.websocket_connect(f"/api/v1/ws/observations?token={token}") as ws:
        # Deactivate user in database
        with TestSession() as session:
            db_user = session.get(User, user.id)
            db_user.is_active = False
            session.commit()

        # The server periodic check will see is_active=False and close the socket
        # Next interaction with socket will raise WebSocketDisconnect(code=1008)
        time.sleep(0.1)
        with pytest.raises(Exception) as exc_info:
            ws.receive_text()
        
        # Verify close code or disconnect
        err_str = str(exc_info.value)
        assert "1008" in err_str or "WebSocketDisconnect" in type(exc_info.value).__name__


def test_jwt_expiration_closes_websocket(test_engine, clean_test_users, monkeypatch):
    """Scenario 5: JWT expiration during an active socket triggers periodic recheck closure (F-010)."""
    import jwt
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("app.api.v1.ws.SessionLocal", TestSession)
    monkeypatch.setattr(settings, "WS_RECHECK_SECONDS", 0.05)

    user = clean_test_users[0]
    # Create token that expires in 1 second
    now = int(time.time())
    payload = {
        "sub": str(user.id),
        "iat": now,
        "exp": now + 1,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
    client = TestClient(app, raise_server_exceptions=False)

    with client.websocket_connect(f"/api/v1/ws/observations?token={token}") as ws:
        # Wait for token to expire and recheck to trigger
        time.sleep(1.1)
        with pytest.raises(Exception) as exc_info:
            ws.receive_text()

        err_str = str(exc_info.value)
        assert "1008" in err_str or "WebSocketDisconnect" in type(exc_info.value).__name__


def test_session_closed_when_query_raises_exception(test_engine, clean_test_users, monkeypatch):
    """Scenario 6: Session closure is guaranteed even if the activity check query raises an exception."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    monkeypatch.setattr("app.api.v1.ws.SessionLocal", TestSession)

    checkout_events = []
    checkin_events = []

    def on_checkout(dbapi_conn, record, proxy):
        checkout_events.append(time.monotonic())

    def on_checkin(dbapi_conn, record):
        checkin_events.append(time.monotonic())

    event.listen(test_engine, "checkout", on_checkout)
    event.listen(test_engine, "checkin", on_checkin)

    from app.api.v1.ws import _user_is_active

    user = clean_test_users[0]

    # Monkeypatch db.get inside _user_is_active to raise an unexpected SQLAlchemyError
    original_get = Session.get

    def failing_get(self, *args, **kwargs):
        raise SQLAlchemyError("Simulated unexpected database failure during activity check")

    monkeypatch.setattr(Session, "get", failing_get)

    try:
        with pytest.raises(SQLAlchemyError):
            _user_is_active(user.id)

        # Assert: Even though an exception was raised, checkin count matches checkout count
        assert len(checkout_events) == len(checkin_events)
        # Assert: Connection pool has 0 checked-out connections
        assert test_engine.pool.checkedout() == 0

    finally:
        event.remove(test_engine, "checkout", on_checkout)
        event.remove(test_engine, "checkin", on_checkin)
