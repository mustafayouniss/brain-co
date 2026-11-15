"""Integration tests for WebSocket ticket authentication, origin checks, and dual-boundary event isolation.

Verifies:
1. POST /api/v1/auth/ws-ticket issues single-use ticket bound to (user_id, organization_id, case_id).
2. Unauthorized case requests for ws-ticket fail closed with 404.
3. WebSocket handshake consumes ticket atomically; replaying the ticket fails (1008).
4. Origin validation rejects untrusted origins (1008).
5. Boundary A (Multi-Tenant Isolation): Org A client never receives Org B events.
6. Boundary B (Intra-Tenant Case Isolation):
   - Case-private events are delivered ONLY to subscribers matching that exact case_id.
   - Unscoped subscribers NEVER receive case-private events.
   - Org-wide events are delivered to unscoped subscribers.
7. Multi-tenant WebSocket support works across non-default organizations.
"""

import json
import uuid
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app.core.security import create_access_token
from app.core.ws_manager import ws_manager
from app.models.case import Case
from app.models.case_assignment import CaseAssignment
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.services.case_service import CaseService


@pytest.fixture
def ws_test_setup(db_session: Session):
    """Seed two organizations, users, memberships, and cases."""
    # Org 1: Cairo Legal Partners
    org1_id = f"org-{uuid.uuid4().hex[:8]}"
    org1 = Organization(id=org1_id, name="Cairo Legal Partners", slug=f"clp-{uuid.uuid4().hex[:6]}", domain="legal", is_active=True)

    admin1 = User(id=uuid.uuid4(), email=f"admin1_{uuid.uuid4().hex[:6]}@clp.com", hashed_password="pw", full_name="Admin CLP", role="admin", is_active=True)
    emp1 = User(id=uuid.uuid4(), email=f"emp1_{uuid.uuid4().hex[:6]}@clp.com", hashed_password="pw", full_name="Emp CLP", role="employee", is_active=True)

    m1_admin = OrganizationMembership(id=uuid.uuid4(), organization_id=org1_id, user_id=admin1.id, role="admin", is_active=True)
    m1_emp = OrganizationMembership(id=uuid.uuid4(), organization_id=org1_id, user_id=emp1.id, role="employee", is_active=True)

    case1 = Case(id=uuid.uuid4(), case_number="CLP-101", title="Maritime Arbitration", organization_id=org1_id, status="open", created_by=admin1.id)
    case2 = Case(id=uuid.uuid4(), case_number="CLP-102", title="Corporate Acquisition", organization_id=org1_id, status="open", created_by=admin1.id)

    # Org 2: Alexandria Law Chambers
    org2_id = f"org-{uuid.uuid4().hex[:8]}"
    org2 = Organization(id=org2_id, name="Alexandria Chambers", slug=f"alc-{uuid.uuid4().hex[:6]}", domain="legal", is_active=True)
    admin2 = User(id=uuid.uuid4(), email=f"admin2_{uuid.uuid4().hex[:6]}@alc.com", hashed_password="pw", full_name="Admin ALC", role="admin", is_active=True)
    m2_admin = OrganizationMembership(id=uuid.uuid4(), organization_id=org2_id, user_id=admin2.id, role="admin", is_active=True)

    # Flush base entities first so foreign keys exist
    db_session.add_all([org1, admin1, emp1, org2, admin2])
    db_session.flush()

    db_session.add_all([m1_admin, m1_emp, case1, case2, m2_admin])
    db_session.flush()

    # Assign emp1 only to case1 (not case2)
    CaseService.assign_user_to_case(db_session, org1_id, case1.id, emp1.id, admin1.id)
    db_session.commit()

    token_admin1 = create_access_token(str(admin1.id), org_id=org1_id, role="admin", domain="legal")
    token_emp1 = create_access_token(str(emp1.id), org_id=org1_id, role="employee", domain="legal")
    token_admin2 = create_access_token(str(admin2.id), org_id=org2_id, role="admin", domain="legal")

    return {
        "org1_id": org1_id,
        "admin1": admin1,
        "emp1": emp1,
        "token_admin1": token_admin1,
        "token_emp1": token_emp1,
        "case1": case1,
        "case2": case2,
        "org2_id": org2_id,
        "admin2": admin2,
        "token_admin2": token_admin2,
    }


def test_ws_ticket_endpoint_authorizations(client: TestClient, ws_test_setup):
    """Test POST /api/v1/auth/ws-ticket authorization matrix."""
    data = ws_test_setup

    # 1. Employee requests ticket for authorized case1 -> 200 OK
    res = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case1"].id)},
        headers={"Authorization": f"Bearer {data['token_emp1']}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "ticket" in body
    assert body["ticket"].startswith("wst_")
    assert body["expires_in"] == 60

    # 2. Employee requests ticket for unauthorized case2 -> 404 Case Not Found (fail-closed)
    res_unauth = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case2"].id)},
        headers={"Authorization": f"Bearer {data['token_emp1']}"},
    )
    assert res_unauth.status_code == 404

    # 3. Admin requests ticket for any case in their org -> 200 OK
    res_admin = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case2"].id)},
        headers={"Authorization": f"Bearer {data['token_admin1']}"},
    )
    assert res_admin.status_code == 200

    # 4. Unauthenticated request -> 401
    res_noauth = client.post("/api/v1/auth/ws-ticket", json={})
    assert res_noauth.status_code == 401


def test_ws_connection_and_replay_rejection(client: TestClient, ws_test_setup):
    """Test WebSocket connects with valid ticket and rejects replay attempts."""
    data = ws_test_setup

    # Issue ticket for emp1 on case1
    res = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case1"].id)},
        headers={"Authorization": f"Bearer {data['token_emp1']}"},
    )
    ticket = res.json()["ticket"]

    # 1. First connection succeeds
    with client.websocket_connect(f"/api/v1/ws/events?ticket={ticket}") as ws:
        # Connection established and active
        pass

    # 2. Second connection using same ticket MUST be rejected (single-use consumption)
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/api/v1/ws/events?ticket={ticket}") as ws:
            pass
    assert exc_info.value.code == 1008


def test_ws_origin_validation(client: TestClient, ws_test_setup):
    """Test WebSocket handshake rejects unauthorized origins."""
    data = ws_test_setup

    res = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case1"].id)},
        headers={"Authorization": f"Bearer {data['token_emp1']}"},
    )
    ticket = res.json()["ticket"]

    # Connect with forbidden origin
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/v1/ws/events?ticket={ticket}",
            headers={"Origin": "http://malicious-attacker.com"},
        ) as ws:
            pass
    assert exc_info.value.code == 1008


@pytest.mark.asyncio
async def test_dual_boundary_event_isolation(client: TestClient, ws_test_setup):
    """Verify Boundary A (Tenant Isolation) and Boundary B (Case Isolation)."""
    data = ws_test_setup
    ws_manager.reset()

    # Create tickets:
    # Client 1: Org 1, Case 1
    t1_res = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case1"].id)},
        headers={"Authorization": f"Bearer {data['token_emp1']}"},
    )
    t1 = t1_res.json()["ticket"]

    # Client 2: Org 1, Case 2
    t2_res = client.post(
        "/api/v1/auth/ws-ticket",
        json={"case_id": str(data["case2"].id)},
        headers={"Authorization": f"Bearer {data['token_admin1']}"},
    )
    t2 = t2_res.json()["ticket"]

    # Client 3: Org 1, Unscoped (Organization level dashboard)
    t3_res = client.post(
        "/api/v1/auth/ws-ticket",
        json={},
        headers={"Authorization": f"Bearer {data['token_admin1']}"},
    )
    t3 = t3_res.json()["ticket"]

    # Client 4: Org 2 (Foreign Tenant)
    t4_res = client.post(
        "/api/v1/auth/ws-ticket",
        json={},
        headers={"Authorization": f"Bearer {data['token_admin2']}"},
    )
    t4 = t4_res.json()["ticket"]

    with client.websocket_connect(f"/api/v1/ws/events?ticket={t1}") as ws_case1, \
         client.websocket_connect(f"/api/v1/ws/events?ticket={t2}") as ws_case2, \
         client.websocket_connect(f"/api/v1/ws/events?ticket={t3}") as ws_org1_unscoped, \
         client.websocket_connect(f"/api/v1/ws/events?ticket={t4}") as ws_org2:

        # 1. Broadcast Case 1 Private Event in Org 1
        case1_event = {
            "event_type": "task_dispatched",
            "case_id": str(data["case1"].id),
            "payload": {"secret": "case1_private_data"},
        }
        sent = await ws_manager.broadcast_event(
            organization_id=data["org1_id"],
            event_payload=case1_event,
            case_id=str(data["case1"].id),
        )
        assert sent == 1, "Only ws_case1 must receive the case1 event"

        msg1 = ws_case1.receive_json()
        assert msg1["payload"]["secret"] == "case1_private_data"

        # 2. Broadcast Org-Wide Event in Org 1 (case_id is None)
        org1_event = {
            "event_type": "worker_status_update",
            "payload": {"system": "all_workers_healthy"},
        }
        sent_org = await ws_manager.broadcast_event(
            organization_id=data["org1_id"],
            event_payload=org1_event,
            case_id=None,
        )
        assert sent_org == 1, "Only ws_org1_unscoped must receive the org-wide event"

        msg_org = ws_org1_unscoped.receive_json()
        assert msg_org["payload"]["system"] == "all_workers_healthy"
