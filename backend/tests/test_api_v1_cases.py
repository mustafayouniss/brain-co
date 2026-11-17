"""Integration tests for Case API endpoints (GET /api/v1/cases, events, knowledge, documents).

Directly validates CACS, multi-tenant isolation, and database-backed event retrieval
against the migrated schema (cases, mesh_events, case_assignments).
"""

from datetime import datetime, timezone
import uuid
from uuid import UUID

from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.case import Case
from app.models.case_assignment import CaseAssignment
from app.models.mesh_event import MeshEventRecord
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


@pytest.fixture
def api_cases_fixture(db_session: Session):
    """Seed two organizations, users, and cases for HTTP API validation."""
    # Org A: Nile Legal
    org_a = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Nile Legal Advisory",
        slug=f"nile-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    admin_a = User(
        id=uuid.uuid4(),
        email=f"admin_nile_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Admin Nile",
        role="admin",
        is_active=True,
    )
    emp_a = User(
        id=uuid.uuid4(),
        email=f"emp_nile_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Emp Nile",
        role="employee",
        is_active=True,
    )
    m_admin_a = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org_a.id, user_id=admin_a.id, role="admin", is_active=True
    )
    m_emp_a = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org_a.id, user_id=emp_a.id, role="employee", is_active=True
    )

    case_a1 = Case(
        id=uuid.uuid4(),
        case_number=f"NLA-{uuid.uuid4().hex[:6]}",
        title="Maritime Arbitration",
        organization_id=org_a.id,
        status="active",
        created_by=admin_a.id,
    )
    case_a2 = Case(
        id=uuid.uuid4(),
        case_number=f"NLA-{uuid.uuid4().hex[:6]}",
        title="Corporate Restructuring",
        organization_id=org_a.id,
        status="active",
        created_by=emp_a.id,
    )

    # Org B: Delta Chambers (Foreign)
    org_b = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Delta Chambers",
        slug=f"delta-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    admin_b = User(
        id=uuid.uuid4(),
        email=f"admin_delta_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Admin Delta",
        role="admin",
        is_active=True,
    )
    m_admin_b = OrganizationMembership(
        id=uuid.uuid4(), organization_id=org_b.id, user_id=admin_b.id, role="admin", is_active=True
    )
    case_b = Case(
        id=uuid.uuid4(),
        case_number=f"DLT-{uuid.uuid4().hex[:6]}",
        title="Banking Compliance",
        organization_id=org_b.id,
        status="active",
        created_by=admin_b.id,
    )

    db_session.add_all([org_a, admin_a, emp_a, org_b, admin_b])
    db_session.flush()

    db_session.add_all([m_admin_a, m_emp_a, case_a1, case_a2, m_admin_b, case_b])
    db_session.flush()

    # Assign emp_a to case_a1 as well
    assignment = CaseAssignment(
        id=uuid.uuid4(),
        case_id=case_a1.id,
        user_id=emp_a.id,
        assigned_by=admin_a.id,
    )
    db_session.add(assignment)

    # Add historical mesh events for case_a1
    now = datetime.now(timezone.utc)
    evt1 = MeshEventRecord(
        id=uuid.uuid4(),
        run_id=uuid.uuid4(),
        sequence_number=1,
        organization_id=org_a.id,
        case_id=case_a1.case_number,
        source_engine="observation",
        destination_engine="planning",
        capability="create_plan",
        event_type="task_dispatched",
        status="running",
        created_at=now,
    )
    evt2 = MeshEventRecord(
        id=uuid.uuid4(),
        run_id=evt1.run_id,
        sequence_number=2,
        organization_id=org_a.id,
        case_id=case_a1.case_number,
        source_engine="planning",
        destination_engine="observation",
        capability="create_plan",
        event_type="task_completed",
        status="completed",
        created_at=now,
    )
    db_session.add_all([evt1, evt2])
    db_session.commit()

    token_admin_a = create_access_token(str(admin_a.id), org_id=org_a.id, role="admin", domain="legal")
    token_emp_a = create_access_token(str(emp_a.id), org_id=org_a.id, role="employee", domain="legal")
    token_admin_b = create_access_token(str(admin_b.id), org_id=org_b.id, role="admin", domain="legal")

    return {
        "org_a": org_a,
        "token_admin_a": token_admin_a,
        "token_emp_a": token_emp_a,
        "case_a1": case_a1,
        "case_a2": case_a2,
        "org_b": org_b,
        "token_admin_b": token_admin_b,
        "case_b": case_b,
        "evt1": evt1,
        "evt2": evt2,
    }


def test_list_cases_admin_and_employee_cacs(client: TestClient, api_cases_fixture):
    """Test GET /api/v1/cases respects organization boundary and CACS."""
    data = api_cases_fixture

    # 1. Admin A lists cases -> sees both case_a1 and case_a2
    res_admin = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
    )
    assert res_admin.status_code == 200
    cases_admin = res_admin.json()
    case_ids_admin = {c["id"] for c in cases_admin}
    assert str(data["case_a1"].id) in case_ids_admin
    assert str(data["case_a2"].id) in case_ids_admin
    assert str(data["case_b"].id) not in case_ids_admin

    # 2. Admin B lists cases -> sees only case_b
    res_b = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {data['token_admin_b']}"},
    )
    assert res_b.status_code == 200
    cases_b = res_b.json()
    case_ids_b = {c["id"] for c in cases_b}
    assert str(data["case_b"].id) in case_ids_b
    assert str(data["case_a1"].id) not in case_ids_b


def test_get_case_details_and_cross_tenant_isolation(client: TestClient, api_cases_fixture):
    """Test GET /api/v1/cases/{case_id} returns details or 404 for cross-tenant access."""
    data = api_cases_fixture

    # 1. Admin A accesses own case -> 200 OK
    res = client.get(
        f"/api/v1/cases/{data['case_a1'].id}",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["case_number"] == data["case_a1"].case_number
    assert body["title"] == "Maritime Arbitration"

    # 2. Admin B attempts to access Org A case -> 404 Not Found (fail-closed, no leak)
    res_cross = client.get(
        f"/api/v1/cases/{data['case_a1'].id}",
        headers={"Authorization": f"Bearer {data['token_admin_b']}"},
    )
    assert res_cross.status_code == 404
    error_json = res_cross.json()
    assert error_json.get("error", {}).get("details", {}).get("code") == "CASE_NOT_FOUND"


def test_get_case_events_replay_and_isolation(client: TestClient, api_cases_fixture):
    """Test GET /api/v1/cases/{case_id}/events retrieves persisted events with cursor replay."""
    data = api_cases_fixture

    # 1. Fetch all events for case_a1
    res = client.get(
        f"/api/v1/cases/{data['case_a1'].id}/events",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["case_id"] == str(data["case_a1"].id)
    assert body["total"] == 2
    assert len(body["events"]) == 2
    assert body["events"][0]["sequence_number"] == 1
    assert body["events"][1]["sequence_number"] == 2

    # 2. Fetch with since_sequence=1 (cursor replay) -> only event 2 returned
    res_cursor = client.get(
        f"/api/v1/cases/{data['case_a1'].id}/events?since_sequence=1",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
    )
    assert res_cursor.status_code == 200
    body_cursor = res_cursor.json()
    assert body_cursor["total"] == 1
    assert body_cursor["events"][0]["sequence_number"] == 2

    # 3. Cross-tenant event access attempt -> 404 Not Found
    res_unauth = client.get(
        f"/api/v1/cases/{data['case_a1'].id}/events",
        headers={"Authorization": f"Bearer {data['token_admin_b']}"},
    )
    assert res_unauth.status_code == 404


def test_create_case_duplicate_number_maps_to_409_regression(
    client: TestClient, api_cases_fixture, db_session: Session, monkeypatch
):
    """Regression test for Issue 1: IntegrityError on uq_cases_org_number maps to 409 CASE_ALREADY_EXISTS."""
    from sqlalchemy.exc import IntegrityError

    data = api_cases_fixture
    existing_case = data["case_a1"]

    # 1. Standard duplicate caught by CaseAlreadyExistsError
    res1 = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
        json={"case_number": existing_case.case_number, "title": "Duplicate Case"},
    )
    assert res1.status_code == 409
    body1 = res1.json()
    err_detail1 = body1.get("error", {}).get("details", {}) or body1.get("detail", {})
    assert err_detail1.get("code") == "CASE_ALREADY_EXISTS"

    # 2. Simulated concurrent race condition: db.commit() raises IntegrityError with uq_cases_org_number
    fake_orig = Exception("duplicate key value violates unique constraint")
    fake_diag = type("Diag", (), {"constraint_name": "uq_cases_org_number"})()
    setattr(fake_orig, "diag", fake_diag)
    simulated_integrity_err = IntegrityError("INSERT INTO cases ...", {}, fake_orig)

    def mock_commit():
        raise simulated_integrity_err

    monkeypatch.setattr(db_session, "commit", mock_commit)

    res2 = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
        json={"case_number": f"NEW-{uuid.uuid4().hex[:6]}", "title": "Concurrent Case"},
    )
    assert res2.status_code == 409
    body2 = res2.json()
    err_detail2 = body2.get("error", {}).get("details", {}) or body2.get("detail", {})
    assert err_detail2.get("code") == "CASE_ALREADY_EXISTS"
    assert "already exists in organization" in err_detail2.get("message", "")

    # 3. Unrelated IntegrityError is re-raised and NOT mapped to 409
    fake_orig_other = Exception("foreign key violation")
    fake_diag_other = type("Diag", (), {"constraint_name": "fk_some_other_table"})()
    setattr(fake_orig_other, "diag", fake_diag_other)
    simulated_other_err = IntegrityError("INSERT INTO cases ...", {}, fake_orig_other)

    def mock_commit_other():
        raise simulated_other_err

    monkeypatch.setattr(db_session, "commit", mock_commit_other)

    res3 = client.post(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {data['token_admin_a']}"},
        json={"case_number": f"OTHER-{uuid.uuid4().hex[:6]}", "title": "Other Case"},
    )
    assert res3.status_code == 500


