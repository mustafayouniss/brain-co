"""Tests for Explicit Case Access Control Strategy (CACS).

Verifies:
1. Organization Admin has access across all cases in the organization.
2. Employee who created the case has access.
3. Employee explicitly assigned to the case has access.
4. Employee NOT assigned to the case is denied access (HTTP 404), even if case status is 'open'.
5. User from Organization B is denied access to Organization A's case (HTTP 404).
6. Revoking case assignment immediately revokes access.
"""

import uuid
import pytest
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.case_assignment import CaseAssignment
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.services.case_service import CaseNotFoundError, CaseService


@pytest.fixture
def cacs_fixture(db_session: Session):
    """Seed two organizations, admins, employees, and cases."""
    # Org A
    org_a = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org A Legal",
        slug=f"org-a-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    admin_a = User(
        id=uuid.uuid4(),
        email=f"admin_a_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Admin A",
        role="admin",
        is_active=True,
    )
    emp_creator_a = User(
        id=uuid.uuid4(),
        email=f"creator_a_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Creator A",
        role="employee",
        is_active=True,
    )
    emp_assigned_a = User(
        id=uuid.uuid4(),
        email=f"assigned_a_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Assigned A",
        role="employee",
        is_active=True,
    )
    emp_unassigned_a = User(
        id=uuid.uuid4(),
        email=f"unassigned_a_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="Unassigned A",
        role="employee",
        is_active=True,
    )

    # Memberships
    m_admin = OrganizationMembership(id=uuid.uuid4(), organization_id=org_a.id, user_id=admin_a.id, role="admin", is_active=True)
    m_creator = OrganizationMembership(id=uuid.uuid4(), organization_id=org_a.id, user_id=emp_creator_a.id, role="employee", is_active=True)
    m_assigned = OrganizationMembership(id=uuid.uuid4(), organization_id=org_a.id, user_id=emp_assigned_a.id, role="employee", is_active=True)
    m_unassigned = OrganizationMembership(id=uuid.uuid4(), organization_id=org_a.id, user_id=emp_unassigned_a.id, role="employee", is_active=True)

    # Case in Org A created by emp_creator_a with status 'open'
    case_a = Case(
        id=uuid.uuid4(),
        case_number=f"CAS-{uuid.uuid4().hex[:6]}",
        title="Dispute Matter Alpha",
        organization_id=org_a.id,
        status="open",
        created_by=emp_creator_a.id,
    )

    # Org B (Foreign)
    org_b = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Org B Legal",
        slug=f"org-b-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    user_b = User(
        id=uuid.uuid4(),
        email=f"user_b_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="pw",
        full_name="User B",
        role="admin",
        is_active=True,
    )
    m_b = OrganizationMembership(id=uuid.uuid4(), organization_id=org_b.id, user_id=user_b.id, role="admin", is_active=True)

    # Add base entities first and flush so foreign keys exist
    db_session.add_all([
        org_a, admin_a, emp_creator_a, emp_assigned_a, emp_unassigned_a,
        org_b, user_b
    ])
    db_session.flush()

    # Add dependent entities
    db_session.add_all([
        m_admin, m_creator, m_assigned, m_unassigned, case_a, m_b
    ])
    db_session.commit()

    # Assign emp_assigned_a to case_a
    CaseService.assign_user_to_case(
        session=db_session,
        organization_id=org_a.id,
        case_id=case_a.id,
        user_id=emp_assigned_a.id,
        assigned_by=admin_a.id,
    )
    db_session.commit()

    return {
        "org_a": org_a,
        "admin_a": admin_a,
        "emp_creator_a": emp_creator_a,
        "emp_assigned_a": emp_assigned_a,
        "emp_unassigned_a": emp_unassigned_a,
        "case_a": case_a,
        "org_b": org_b,
        "user_b": user_b,
    }


def test_admin_has_case_access(db_session: Session, cacs_fixture):
    """Admin has full access to any case in their organization."""
    data = cacs_fixture
    case = CaseService.validate_case_access(
        session=db_session,
        organization_id=data["org_a"].id,
        user_id=data["admin_a"].id,
        user_role="admin",
        case_id_or_number=data["case_a"].id,
    )
    assert case.id == data["case_a"].id


def test_creator_has_case_access(db_session: Session, cacs_fixture):
    """Employee creator has access to case they created."""
    data = cacs_fixture
    case = CaseService.validate_case_access(
        session=db_session,
        organization_id=data["org_a"].id,
        user_id=data["emp_creator_a"].id,
        user_role="employee",
        case_id_or_number=data["case_a"].case_number,
    )
    assert case.id == data["case_a"].id


def test_assigned_employee_has_case_access(db_session: Session, cacs_fixture):
    """Employee explicitly assigned to case has access."""
    data = cacs_fixture
    case = CaseService.validate_case_access(
        session=db_session,
        organization_id=data["org_a"].id,
        user_id=data["emp_assigned_a"].id,
        user_role="employee",
        case_id_or_number=data["case_a"].id,
    )
    assert case.id == data["case_a"].id


def test_unassigned_employee_denied_even_if_status_is_open(db_session: Session, cacs_fixture):
    """Case status such as 'open' must NEVER independently grant access.

    Unassigned employee must be rejected with CaseNotFoundError (404).
    """
    data = cacs_fixture
    assert data["case_a"].status == "open"

    with pytest.raises(CaseNotFoundError):
        CaseService.validate_case_access(
            session=db_session,
            organization_id=data["org_a"].id,
            user_id=data["emp_unassigned_a"].id,
            user_role="employee",
            case_id_or_number=data["case_a"].id,
        )


def test_cross_tenant_case_access_denied(db_session: Session, cacs_fixture):
    """User from Organization B is denied access to Organization A's case."""
    data = cacs_fixture
    with pytest.raises(CaseNotFoundError):
        CaseService.validate_case_access(
            session=db_session,
            organization_id=data["org_b"].id,  # Asking from Org B context
            user_id=data["user_b"].id,
            user_role="admin",
            case_id_or_number=data["case_a"].id,  # Belonging to Org A
        )


def test_revoked_assignment_immediately_revokes_access(db_session: Session, cacs_fixture):
    """Deleting case assignment immediately causes validate_case_access to fail closed."""
    data = cacs_fixture
    # Verify access before revocation
    case = CaseService.validate_case_access(
        session=db_session,
        organization_id=data["org_a"].id,
        user_id=data["emp_assigned_a"].id,
        user_role="employee",
        case_id_or_number=data["case_a"].id,
    )
    assert case is not None

    # Revoke assignment
    db_session.query(CaseAssignment).filter(
        CaseAssignment.case_id == data["case_a"].id,
        CaseAssignment.user_id == data["emp_assigned_a"].id,
    ).delete()
    db_session.commit()

    # Access must now fail closed
    with pytest.raises(CaseNotFoundError):
        CaseService.validate_case_access(
            session=db_session,
            organization_id=data["org_a"].id,
            user_id=data["emp_assigned_a"].id,
            user_role="employee",
            case_id_or_number=data["case_a"].id,
        )
