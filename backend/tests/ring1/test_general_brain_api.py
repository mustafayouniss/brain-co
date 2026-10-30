"""Comprehensive tests for Ring 1 General Brain API Contracts (Section 17).

Covers:
- GET /api/v1/brain/status
- POST /api/v1/observations
- GET /api/v1/observations
- POST /api/v1/context/resolve
- GET /api/v1/memory/{id}
- GET /api/v1/retrieval/search
- WS /api/v1/ws/observations
"""

from __future__ import annotations

import json
import uuid
from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.ring1.models.observation import MemoryRecord, Observation


@pytest.fixture
def auth_user(db_session: Session) -> User:
    """Create a standard active user for testing."""
    user = User(
        email=f"user_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Brain Tester",
        hashed_password=hash_password("password12345"),
        role="employee",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """Create an active admin user with validation authority."""
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Brain Admin",
        hashed_password=hash_password("adminpass12345"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def auth_headers(auth_user: User) -> dict[str, str]:
    token = create_access_token(str(auth_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. GET /api/v1/brain/status
# ---------------------------------------------------------------------------

def test_brain_status_endpoint(client: TestClient):
    """GET /api/v1/brain/status returns General Brain status, 6 engines, capabilities, and domains."""
    response = client.get("/api/v1/brain/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["planning_advisory"] is True
    assert set(data["engines"]) == {
        "perception",
        "observation",
        "context",
        "memory",
        "retrieval",
        "planning",
    }
    assert len(data["registered_capabilities"]) >= 9
    assert "legal" in data["registered_domains"]
    assert "sales" in data["registered_domains"]
    assert "logistics" in data["registered_domains"]


# ---------------------------------------------------------------------------
# 2. POST /api/v1/observations & GET /api/v1/observations
# ---------------------------------------------------------------------------

def test_create_and_list_observations(client: TestClient, auth_headers: dict[str, str]):
    """POST /api/v1/observations creates observation and GET /api/v1/observations lists it."""
    case_id = f"case-{uuid.uuid4().hex[:8]}"
    obs_payload = {
        "event_type": "contract.uploaded",
        "source": "api_test",
        "case_id": case_id,
        "payload": {"title": "Service Level Agreement", "pages": 12},
        "idempotency_key": f"key-{uuid.uuid4()}",
    }

    # 1. Create Observation
    post_res = client.post("/api/v1/observations", json=obs_payload, headers=auth_headers)
    assert post_res.status_code == 201
    post_data = post_res.json()
    assert post_data["event_type"] == "contract.uploaded"
    assert post_data["case_id"] == case_id
    assert post_data["status"] == "recorded"
    assert post_data["organization_id"] == getattr(settings, "ORGANIZATION_ID", "org-brain-corp")

    # 2. Idempotent repeat returns existing
    repeat_res = client.post("/api/v1/observations", json=obs_payload, headers=auth_headers)
    assert repeat_res.status_code == 201
    assert repeat_res.json()["id"] == post_data["id"]

    # 3. List observations filtered by type
    get_res = client.get(
        "/api/v1/observations",
        params={"type": "contract.uploaded", "limit": 10},
        headers={**auth_headers, "X-Case-ID": case_id},
    )
    assert get_res.status_code == 200
    list_data = get_res.json()
    assert len(list_data["items"]) >= 1
    assert any(item["id"] == post_data["id"] for item in list_data["items"])


def test_observation_cursor_pagination(client: TestClient, auth_headers: dict[str, str]):
    """Verify keyset cursor pagination with stable deterministic order."""
    case_id = f"cursor-case-{uuid.uuid4().hex[:8]}"

    # Create 3 observations
    for i in range(3):
        client.post(
            "/api/v1/observations",
            json={
                "event_type": "step.executed",
                "source": "pagination_test",
                "case_id": case_id,
                "payload": {"step": i},
                "idempotency_key": f"p-key-{case_id}-{i}",
            },
            headers=auth_headers,
        )

    # First page with limit=2
    res_page1 = client.get(
        "/api/v1/observations",
        params={"type": "step.executed", "limit": 2},
        headers={**auth_headers, "X-Case-ID": case_id},
    )
    assert res_page1.status_code == 200
    data_page1 = res_page1.json()
    assert len(data_page1["items"]) == 2
    assert data_page1["has_more"] is True
    assert data_page1["next_cursor"] is not None

    # Second page using next_cursor
    res_page2 = client.get(
        "/api/v1/observations",
        params={"type": "step.executed", "limit": 2, "cursor": data_page1["next_cursor"]},
        headers={**auth_headers, "X-Case-ID": case_id},
    )
    assert res_page2.status_code == 200
    data_page2 = res_page2.json()
    assert len(data_page2["items"]) == 1
    # Verify no item duplication across pages
    page1_ids = {item["id"] for item in data_page1["items"]}
    page2_ids = {item["id"] for item in data_page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)


# ---------------------------------------------------------------------------
# 3. POST /api/v1/context/resolve
# ---------------------------------------------------------------------------

def test_context_resolve_endpoint(client: TestClient, auth_headers: dict[str, str]):
    """POST /api/v1/context/resolve resolves execution boundaries."""
    case_id = f"case-{uuid.uuid4().hex[:8]}"
    resolve_req = {
        "domain_id": "legal",
        "case_id": case_id,
        "hints": {"workflow": "intake"},
    }

    response = client.post("/api/v1/context/resolve", json=resolve_req, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resolution_status"] in ("explicit", "resolved")
    assert data["case_id"] == case_id
    assert data["domain_id"] == "legal"
    assert data["organization_id"] == getattr(settings, "ORGANIZATION_ID", "org-brain-corp")


# ---------------------------------------------------------------------------
# 4. GET /api/v1/memory/{id}
# ---------------------------------------------------------------------------

def test_get_memory_record_endpoint(client: TestClient, db_session: Session, auth_headers: dict[str, str]):
    """GET /api/v1/memory/{id} retrieves authorized records and enforces strict isolation."""
    case_a = f"case-mem-a-{uuid.uuid4().hex[:6]}"
    case_b = f"case-mem-b-{uuid.uuid4().hex[:6]}"
    org_id = getattr(settings, "ORGANIZATION_ID", "org-brain-corp")

    # Record in case_a
    rec_a = MemoryRecord(
        id=uuid.uuid4(),
        record_type="client_statement",
        case_id=case_a,
        organization_id=org_id,
        payload={"statement": "Defendant agreed to settle for 500k EGP"},
        status="active",
    )
    # Record in other organization
    rec_other_org = MemoryRecord(
        id=uuid.uuid4(),
        record_type="client_statement",
        case_id=case_a,
        organization_id="org-foreign-intruder",
        payload={"secret": "foreign data"},
        status="active",
    )
    db_session.add(rec_a)
    db_session.add(rec_other_org)
    db_session.flush()

    # 1. Authorized read with matching case -> 200 OK
    res_ok = client.get(
        f"/api/v1/memory/{rec_a.id}",
        headers={**auth_headers, "X-Case-ID": case_a},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["payload"]["statement"] == "Defendant agreed to settle for 500k EGP"

    # 2. Cross-case read attempt -> 404 Not Found (sanitized, zero existence leak)
    res_cross_case = client.get(
        f"/api/v1/memory/{rec_a.id}",
        headers={**auth_headers, "X-Case-ID": case_b},
    )
    assert res_cross_case.status_code == 404

    # 3. Cross-tenant read attempt -> 404 Not Found (sanitized)
    res_cross_org = client.get(
        f"/api/v1/memory/{rec_other_org.id}",
        headers={**auth_headers, "X-Case-ID": case_a},
    )
    assert res_cross_org.status_code == 404

    # 4. Non-existent record -> 404 Not Found
    res_not_found = client.get(
        f"/api/v1/memory/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert res_not_found.status_code == 404


# ---------------------------------------------------------------------------
# 5. GET /api/v1/retrieval/search
# ---------------------------------------------------------------------------

def test_retrieval_search_endpoint(client: TestClient, db_session: Session, auth_headers: dict[str, str]):
    """GET /api/v1/retrieval/search searches records enforcing case boundary and candidate exclusion."""
    case_id = f"case-search-{uuid.uuid4().hex[:6]}"
    other_case = f"case-search-{uuid.uuid4().hex[:6]}"
    org_id = getattr(settings, "ORGANIZATION_ID", "org-brain-corp")

    # Validated active record in target case
    rec_target = MemoryRecord(
        id=uuid.uuid4(),
        record_type="contract_fact",
        case_id=case_id,
        organization_id=org_id,
        payload={"text": "Arbitration clause specifies Cairo Regional Centre (CRCICA)."},
        status="active",
    )
    # Candidate unvalidated record in target case (MUST BE EXCLUDED)
    rec_candidate = MemoryRecord(
        id=uuid.uuid4(),
        record_type="unvalidated_signal",
        case_id=case_id,
        organization_id=org_id,
        payload={"text": "Arbitration hearsay discussion."},
        status="candidate",
    )
    # Record in another case with matching keyword (MUST BE ISOLATED)
    rec_other_case = MemoryRecord(
        id=uuid.uuid4(),
        record_type="contract_fact",
        case_id=other_case,
        organization_id=org_id,
        payload={"text": "Arbitration clause for competitor."},
        status="active",
    )

    db_session.add(rec_target)
    db_session.add(rec_candidate)
    db_session.add(rec_other_case)
    db_session.flush()

    # Search query "Arbitration" with X-Case-ID boundary
    res = client.get(
        "/api/v1/retrieval/search",
        params={"q": "Arbitration"},
        headers={**auth_headers, "X-Case-ID": case_id},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_found"] == 1
    assert data["items"][0]["record_id"] == str(rec_target.id)

    # Empty query terms returns 400
    res_empty = client.get(
        "/api/v1/retrieval/search",
        params={"q": "   "},
        headers=auth_headers,
    )
    assert res_empty.status_code == 422 or res_empty.status_code == 400


# ---------------------------------------------------------------------------
# 6. WS /api/v1/ws/observations
# ---------------------------------------------------------------------------

def test_websocket_observations_authentication_and_broadcast(client: TestClient, auth_user: User, auth_headers: dict[str, str]):
    """WS /api/v1/ws/observations rejects unauthenticated clients and streams events to authenticated clients."""
    # 1. Unauthenticated connection is rejected
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/observations") as ws:
            pass

    # 2. Authenticated connection
    token = create_access_token(str(auth_user.id))
    case_id = f"ws-case-{uuid.uuid4().hex[:6]}"

    with client.websocket_connect(f"/api/v1/ws/observations?token={token}&case_id={case_id}") as ws:
        # Post observation via HTTP API while WebSocket is connected
        obs_res = client.post(
            "/api/v1/observations",
            json={
                "event_type": "realtime.alert",
                "source": "ws_test",
                "case_id": case_id,
                "payload": {"message": "Critical deadline approaching"},
            },
            headers=auth_headers,
        )
        assert obs_res.status_code == 201

        # Receive streamed event on WebSocket
        msg_text = ws.receive_text()
        msg = json.loads(msg_text)
        assert msg["type"] == "observation.created"
        assert msg["data"]["event_type"] == "realtime.alert"
        assert msg["data"]["case_id"] == case_id
        assert msg["data"]["payload"]["message"] == "Critical deadline approaching"
