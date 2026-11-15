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


def test_ring1_knowledge_rejects_mismatched_organization_id(client):
    """GET /api/v1/ring1/knowledge with mismatched organization_id returns 403."""
    response = client.get(
        "/api/v1/ring1/knowledge",
        params={"organization_id": "evil-org", "case_id": "c1", "query": "x"},
    )
    assert response.status_code == 403
    err_body = response.json()
    err_msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "organization_id does not match this deployment." in err_msg


def test_ring1_test_run_with_scoped_case_success(client, admin_headers, db_session):
    """POST /api/v1/ring1/test-run succeeds with verified case_id under CACS."""
    from app.models.case import Case
    from app.models.organization import Organization, OrganizationMembership

    org_id = f"org-test-{uuid.uuid4().hex[:6]}"
    org = Organization(id=org_id, name="Test Org", slug=f"test-slug-{uuid.uuid4().hex[:4]}", domain="legal")
    db_session.add(org)

    # Decode admin user id
    token = admin_headers["Authorization"].split(" ")[1]
    from app.core.security import decode_access_token, create_access_token
    payload = decode_access_token(token)
    user_id = uuid.UUID(payload["sub"])

    # Add admin membership
    membership = OrganizationMembership(organization_id=org_id, user_id=user_id, role="admin")
    db_session.add(membership)

    # Create case
    case = Case(
        id=uuid.uuid4(),
        case_number=f"CAS-{uuid.uuid4().hex[:4]}",
        title="Scoped Test Case",
        organization_id=org_id,
        created_by=user_id,
        status="open",
    )
    db_session.add(case)
    db_session.commit()

    # Reissue token with org_id
    scoped_token = create_access_token(str(user_id), org_id=org_id, role="admin")
    headers = {"Authorization": f"Bearer {scoped_token}"}

    res = client.post(
        "/api/v1/ring1/test-run",
        json={"mode": "custom_prompt", "custom_prompt": "Audit contract clause", "case_id": str(case.id), "stream": False},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["run_id"].startswith("run-")
    assert len(data["events"]) >= 3
    # Check that events carry organization_id and case_id
    assert any(e.get("case_id") for e in data["events"])


def test_ring1_test_run_with_nonexistent_case_fails_closed(client, admin_headers):
    """POST /api/v1/ring1/test-run with non-existent case fails closed with 404."""
    res = client.post(
        "/api/v1/ring1/test-run",
        json={"mode": "custom_prompt", "custom_prompt": "Audit clause", "case_id": "00000000-0000-0000-0000-000000000000", "stream": False},
        headers=admin_headers,
    )
    assert res.status_code == 404
    body = res.json()
    msg = body.get("detail") or body.get("error", {}).get("message", "")
    assert "not found or access denied" in msg.lower()


def test_ring1_test_run_with_mismatched_org_fails_403(client, admin_headers):
    """POST /api/v1/ring1/test-run with mismatched organization_id returns 403."""
    from app.core.security import decode_access_token, create_access_token
    token = admin_headers["Authorization"].split(" ")[1]
    payload = decode_access_token(token)
    user_id = payload["sub"]

    scoped_token = create_access_token(str(user_id), org_id="org-real-tenant", role="admin")
    headers = {"Authorization": f"Bearer {scoped_token}"}

    res = client.post(
        "/api/v1/ring1/test-run",
        json={"mode": "e2e", "organization_id": "org-spoofed-attacker", "stream": False},
        headers=headers,
    )
    assert res.status_code == 403


