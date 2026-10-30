"""Tests for Ring 1 Live Test & Observability API endpoints (/api/v1/ring1)."""

from __future__ import annotations

import json
from unittest.mock import patch
import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an active admin user."""
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Ring1 Admin",
        hashed_password=hash_password("adminpassword1234"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


def test_ring1_capabilities_endpoint(client):
    """GET /api/v1/ring1/capabilities returns 200 with engine statuses and capability list."""
    response = client.get("/api/v1/ring1/capabilities")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["protocol_version"] == "1.0"
    assert len(data["engines"]) == 6
    assert "perception.structure_input" in data["capabilities"]
    assert "planning.request_replan" in data["capabilities"]


def test_ring1_test_run_e2e_non_streaming(client):
    """POST /api/v1/ring1/test-run (mode=e2e, stream=False) executes all 6 engines."""
    payload = {"mode": "e2e", "stream": False}
    response = client.post("/api/v1/ring1/test-run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["run_id"].startswith("run-")
    events = data["events"]
    assert len(events) >= 8

    summary = data["summary"]
    invoked = set(summary["invoked_engines"])
    assert "perception" in invoked
    assert "observation" in invoked
    assert "context" in invoked
    assert "memory" in invoked
    assert "retrieval" in invoked
    assert "planning" in invoked
    assert len(summary["delegation_edges"]) > 0


def test_ring1_test_run_force_failure_non_streaming(client):
    """POST /api/v1/ring1/test-run (mode=force_failure, stream=False) executes replan lifecycle."""
    payload = {"mode": "force_failure", "stream": False}
    response = client.post("/api/v1/ring1/test-run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    summary = data["summary"]
    replan_payload = summary.get("replanned_payload")
    assert replan_payload is not None
    assert replan_payload["old_version"] == 1
    assert replan_payload["new_version"] == 2
    assert len(replan_payload["steps_retained"]) >= 1


def test_ring1_test_run_streaming_sse(client):
    """POST /api/v1/ring1/test-run (mode=e2e, stream=True) returns SSE data stream."""
    payload = {"mode": "e2e", "stream": True}
    response = client.post("/api/v1/ring1/test-run", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line.strip() for line in response.text.split("\n") if line.startswith("data:")]
    assert len(lines) >= 8
    first_event = json.loads(lines[0].replace("data:", "").strip())
    assert first_event["sequence"] == 1
    assert first_event["destination_engine"] == "perception"


def test_ring1_get_test_run_and_list(client):
    """GET /api/v1/ring1/test-runs/{run_id} and GET /api/v1/ring1/test-runs retrieve stored runs."""
    # 1. Run a test to ensure at least one run is in the registry
    run_resp = client.post("/api/v1/ring1/test-run", json={"mode": "e2e", "stream": False})
    run_id = run_resp.json()["run_id"]

    # 2. Retrieve by ID
    get_resp = client.get(f"/api/v1/ring1/test-runs/{run_id}")
    assert get_resp.status_code == 200
    run_data = get_resp.json()
    assert run_data["run_id"] == run_id
    assert run_data["mode"] == "e2e"
    assert len(run_data["events"]) >= 8

    # 3. List recent runs
    list_resp = client.get("/api/v1/ring1/test-runs?limit=10")
    assert list_resp.status_code == 200
    runs = list_resp.json()
    assert any(r["run_id"] == run_id for r in runs)


def test_ring1_get_test_run_not_found(client):
    """GET /api/v1/ring1/test-runs/nonexistent returns 404."""
    response = client.get("/api/v1/ring1/test-runs/run-nonexistent-12345")
    assert response.status_code == 404


def test_ring1_production_environment_requires_admin(client, admin_headers):
    """In production mode, anonymous or employee access is blocked; admin is allowed."""
    with patch.object(settings, "ENVIRONMENT", "production"):
        # Without headers -> 401
        res_anon = client.get("/api/v1/ring1/capabilities")
        assert res_anon.status_code == 401

        # With admin headers -> 200
        res_admin = client.get("/api/v1/ring1/capabilities", headers=admin_headers)
        assert res_admin.status_code == 200
