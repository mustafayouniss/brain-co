"""Regression tests for Round 2 Tenant Isolation fixes.

Verifies:
1. ITEM 1 (ws.py): WebSocket with a case_id that does not exist in caller's organization
   is rejected with 1008, and a case that exists only in another organization is also
   rejected with 1008. Non-UUID strings that do not match a case in the organization also close with 1008.
2. ITEM 2 (test_scenario_service.py): The scenario runner does not bind to another
   organization's case even if its UUID is passed as active_case.
3. ITEM 3 (ring1.py): A token without org claim cannot make /ring1/test-run use an
   organization from the client request body (returns 403 on mismatch with verified default).
4. ITEM 4 (ring1.py): An employee not assigned to a case gets 404 from GET /ring1/knowledge.
   An explicit organization mismatch returns 403 before the case access check.
"""

from __future__ import annotations

import uuid
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.core.security import create_access_token, hash_password
from app.models.case import Case
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.ring1.models.observation import MemoryRecord
from app.ring1.service import Ring1TestRunner
from app.ring1.services.test_scenario_service import TestScenarioService
from app.services.case_service import CaseService


def test_ws_rejects_nonexistent_and_cross_tenant_case_ids(client: TestClient, db_session: Session):
    """ITEM 1 regression: WebSocket with invalid or foreign case_id is rejected with 1008."""
    # 1. Create Org 1, User 1 first, flush, then Case 1
    org1 = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org One",
        slug=f"org1-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org1)
    db_session.flush()

    user1 = User(
        id=uuid.uuid4(),
        email=f"ws_user1_{uuid.uuid4().hex[:6]}@org1.com",
        hashed_password=hash_password("pw1"),
        full_name="User One",
        role="admin",
        is_active=True,
    )
    db_session.add(user1)
    db_session.flush()

    m1 = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org1.id, user_id=user1.id, role="admin", is_active=True
    )
    db_session.add(m1)
    db_session.flush()

    case1 = Case(
        id=uuid.uuid4(),
        case_number=f"CAS1-{uuid.uuid4().hex[:6]}",
        title="Case 1 in Org 1",
        organization_id=org1.id,
        status="active",
        created_by=user1.id,
    )
    db_session.add(case1)
    db_session.flush()

    # 2. Create Org 2, User 2 first, flush, then Case 2
    org2 = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org Two",
        slug=f"org2-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org2)
    db_session.flush()

    user2 = User(
        id=uuid.uuid4(),
        email=f"ws_user2_{uuid.uuid4().hex[:6]}@org2.com",
        hashed_password=hash_password("pw2"),
        full_name="User Two",
        role="admin",
        is_active=True,
    )
    db_session.add(user2)
    db_session.flush()

    m2 = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org2.id, user_id=user2.id, role="admin", is_active=True
    )
    db_session.add(m2)
    db_session.flush()

    case2 = Case(
        id=uuid.uuid4(),
        case_number=f"CAS2-{uuid.uuid4().hex[:6]}",
        title="Case 2 in Org 2",
        organization_id=org2.id,
        status="active",
        created_by=user2.id,
    )
    db_session.add(case2)
    db_session.commit()

    token1 = create_access_token(str(user1.id), org_id=org1.id, role="admin", domain="legal")

    # A. Case exists only in foreign organization (Org 2) -> must reject with 1008
    with pytest.raises(WebSocketDisconnect) as exc_info_foreign:
        with client.websocket_connect(f"/api/v1/ws/observations?token={token1}&case_id={case2.id}"):
            pass
    assert exc_info_foreign.value.code == 1008

    # B. Non-existent random UUID case -> must reject with 1008
    random_uuid = uuid.uuid4()
    with pytest.raises(WebSocketDisconnect) as exc_info_random:
        with client.websocket_connect(f"/api/v1/ws/observations?token={token1}&case_id={random_uuid}"):
            pass
    assert exc_info_random.value.code == 1008

    # C. Arbitrary non-UUID string that does not match case_number in Org 1 -> must reject with 1008
    with pytest.raises(WebSocketDisconnect) as exc_info_non_uuid:
        with client.websocket_connect(f"/api/v1/ws/observations?token={token1}&case_id=non-existent-case"):
            pass
    assert exc_info_non_uuid.value.code == 1008

    # D. Legitimate case in caller's own organization -> succeeds
    with client.websocket_connect(f"/api/v1/ws/observations?token={token1}&case_id={case1.id}"):
        pass


def test_scenario_service_does_not_bind_to_foreign_organization_case(db_session: Session):
    """ITEM 2 regression: TestScenarioService does not bind to another organization's case."""
    # Org 1: Local tenant
    org1 = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Local Tenant Org",
        slug=f"local-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org1)
    db_session.flush()

    user1 = User(
        id=uuid.uuid4(),
        email=f"scenario_u1_{uuid.uuid4().hex[:6]}@local.com",
        hashed_password=hash_password("pw"),
        full_name="Local User",
        role="admin",
        is_active=True,
    )
    db_session.add(user1)
    db_session.flush()

    # Org 2: Foreign tenant with existing case
    org2 = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Foreign Tenant Org",
        slug=f"foreign-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org2)
    db_session.flush()

    user2 = User(
        id=uuid.uuid4(),
        email=f"scenario_u2_{uuid.uuid4().hex[:6]}@foreign.com",
        hashed_password=hash_password("pw"),
        full_name="Foreign User",
        role="admin",
        is_active=True,
    )
    db_session.add(user2)
    db_session.flush()

    foreign_case = Case(
        id=uuid.uuid4(),
        case_number=f"FOREIGN-{uuid.uuid4().hex[:6]}",
        title="Sensitive Foreign Acquisition",
        organization_id=org2.id,
        status="active",
        created_by=user2.id,
    )
    db_session.add(foreign_case)
    db_session.commit()

    org1_id = org1.id
    org2_id = org2.id
    foreign_case_id = foreign_case.id

    runner = Ring1TestRunner(db_session=db_session)
    scenario_service = TestScenarioService(runner=runner)

    # Execute scenario for org1 passing foreign_case.id as active_case
    events = []
    import asyncio
    async def _run():
        async for evt in scenario_service.execute(
            mode="e2e",
            custom_prompt="Verify cross-tenant binding",
            organization_id=org1_id,
            case_id=str(foreign_case_id),
        ):
            events.append(evt)

    asyncio.run(_run())

    # Verify foreign_case still strictly belongs to org2 and was NOT rebound
    fc = db_session.get(Case, foreign_case_id)
    assert fc is not None
    assert fc.organization_id == org2_id

    # Verify that if a case with foreign_case_id string was created in org1, it is isolated
    org1_cases = db_session.query(Case).filter(Case.organization_id == org1_id).all()
    for c in org1_cases:
        assert c.id != foreign_case_id
        assert c.organization_id == org1_id


def test_token_without_org_cannot_use_body_organization_in_test_run(client: TestClient, db_session: Session):
    """ITEM 3 regression: Token without org claim cannot force /ring1/test-run to use org from body."""
    user = User(
        id=uuid.uuid4(),
        email=f"no_org_operator_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("pw"),
        full_name="No Org Operator",
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Generate token without org_id / organization_id claim
    token_no_org = create_access_token(str(user.id))
    headers = {"Authorization": f"Bearer {token_no_org}"}

    # Attempt to use spoofed organization_id in request body
    res = client.post(
        "/api/v1/ring1/test-run",
        json={"mode": "e2e", "organization_id": "org-spoofed-in-body", "stream": False},
        headers=headers,
    )
    assert res.status_code == 403
    err_body = res.json()
    err_msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "Organization mismatch" in err_msg


def test_unassigned_employee_gets_404_from_knowledge_endpoint(client: TestClient, db_session: Session):
    """ITEM 4 regression: Unassigned employee gets 404 from GET /ring1/knowledge."""
    org = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Knowledge Test Org",
        slug=f"ktest-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    db_session.add(org)
    db_session.flush()

    # User 1: Admin (creates case)
    admin = User(
        id=uuid.uuid4(),
        email=f"k_admin_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("pw"),
        full_name="Knowledge Admin",
        role="admin",
        is_active=True,
    )
    # User 2: Employee not assigned
    emp_unassigned = User(
        id=uuid.uuid4(),
        email=f"k_unassigned_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("pw"),
        full_name="Unassigned Emp",
        role="employee",
        is_active=True,
    )
    # User 3: Employee assigned
    emp_assigned = User(
        id=uuid.uuid4(),
        email=f"k_assigned_{uuid.uuid4().hex[:6]}@example.com",
        hashed_password=hash_password("pw"),
        full_name="Assigned Emp",
        role="employee",
        is_active=True,
    )
    db_session.add_all([admin, emp_unassigned, emp_assigned])
    db_session.flush()

    m_admin = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org.id, user_id=admin.id, role="admin", is_active=True
    )
    m_unassigned = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org.id, user_id=emp_unassigned.id, role="employee", is_active=True
    )
    m_assigned = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org.id, user_id=emp_assigned.id, role="employee", is_active=True
    )
    db_session.add_all([m_admin, m_unassigned, m_assigned])
    db_session.flush()

    case = Case(
        id=uuid.uuid4(),
        case_number=f"KNOW-{uuid.uuid4().hex[:6]}",
        title="Knowledge Confidential Case",
        organization_id=org.id,
        status="active",
        created_by=admin.id,
    )
    db_session.add(case)
    db_session.flush()

    # Assign emp_assigned to case
    CaseService.assign_user_to_case(db_session, org.id, case.id, emp_assigned.id, admin.id)

    # Seed a memory record for the case
    rec = MemoryRecord(
        id=uuid.uuid4(),
        organization_id=org.id,
        case_id=str(case.id),
        record_type="pdf_knowledge",
        status="candidate",
        payload={"title": "Test Confidential Facts", "facts": []},
    )
    db_session.add(rec)
    db_session.commit()

    token_unassigned = create_access_token(str(emp_unassigned.id), org_id=org.id, role="employee", domain="legal")
    token_assigned = create_access_token(str(emp_assigned.id), org_id=org.id, role="employee", domain="legal")

    # 1. Unassigned employee receives 404 (fail-closed, does not reveal existence)
    res_unassigned = client.get(
        f"/api/v1/ring1/knowledge?case_id={case.id}",
        headers={"Authorization": f"Bearer {token_unassigned}"},
    )
    assert res_unassigned.status_code == 404

    # 2. Assigned employee receives 200 OK
    res_assigned = client.get(
        f"/api/v1/ring1/knowledge?case_id={case.id}",
        headers={"Authorization": f"Bearer {token_assigned}"},
    )
    assert res_assigned.status_code == 200
    body = res_assigned.json()
    assert body["case_id"] == str(case.id)

    # 3. Mismatched organization_id returns 403 BEFORE reaching case access validation
    res_mismatch = client.get(
        f"/api/v1/ring1/knowledge?case_id={case.id}&organization_id=foreign-org-mismatch",
        headers={"Authorization": f"Bearer {token_unassigned}"},
    )
    assert res_mismatch.status_code == 403
    err_body = res_mismatch.json()
    err_msg = err_body.get("detail") or err_body.get("error", {}).get("message", "")
    assert "organization_id does not match this deployment" in err_msg
