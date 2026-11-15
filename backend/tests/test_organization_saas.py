"""Automated test suite verifying multi-tenant Organization Signup, Authentication, and Context."""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


def test_register_organization_success(client: TestClient, db_session: Session):
    suffix = uuid.uuid4().hex[:6]
    payload = {
        "company_name": f"Cairo Legal Partners {suffix}",
        "admin_email": f"admin_{suffix}@cairolegal.com",
        "admin_full_name": "Tarek Mansour",
        "password": "SecurePassword123!",
        "domain": "legal",
    }
    resp = client.post("/api/v1/auth/register-organization", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["organization"]["name"] == f"Cairo Legal Partners {suffix}"
    assert data["organization"]["domain"] == "legal"
    assert data["user"]["email"] == f"admin_{suffix}@cairolegal.com"
    assert data["membership"]["role"] == "admin"
    assert "access_token" in data

    token_payload = decode_access_token(data["access_token"])
    assert token_payload["org_id"] == data["organization"]["id"]
    assert token_payload["role"] == "admin"
    assert token_payload["domain"] == "legal"

    # Verify database persistence
    db_session.expire_all()
    org = db_session.query(Organization).filter(Organization.id == data["organization"]["id"]).first()
    assert org is not None
    assert org.name == f"Cairo Legal Partners {suffix}"

    user = db_session.query(User).filter(User.email == f"admin_{suffix}@cairolegal.com").first()
    assert user is not None
    assert user.role == "admin"

    membership = db_session.query(OrganizationMembership).filter(
        OrganizationMembership.organization_id == org.id,
        OrganizationMembership.user_id == user.id,
    ).first()
    assert membership is not None
    assert membership.role == "admin"


def test_register_organization_duplicate_email(client: TestClient):
    suffix = uuid.uuid4().hex[:6]
    payload = {
        "company_name": f"Alexandria Law Firm {suffix}",
        "admin_email": f"dup_{suffix}@alexlaw.com",
        "admin_full_name": "Samir Amin",
        "password": "SecurePassword123!",
        "domain": "legal",
    }
    resp1 = client.post("/api/v1/auth/register-organization", json=payload)
    assert resp1.status_code == 201

    # Second registration with same email fails
    resp2 = client.post("/api/v1/auth/register-organization", json=payload)
    assert resp2.status_code == 409
    err_msg = resp2.json().get("error", {}).get("message") or resp2.json().get("detail", "")
    assert "already exists" in err_msg.lower()


def test_login_and_me_organization_context(client: TestClient):
    suffix = uuid.uuid4().hex[:6]
    admin_email = f"tarek_{suffix}@nilelegal.com"
    reg_payload = {
        "company_name": f"Nile Legal Advisory {suffix}",
        "admin_email": admin_email,
        "admin_full_name": "Tarek Nile",
        "password": "Password123!",
        "domain": "legal",
    }
    reg_resp = client.post("/api/v1/auth/register-organization", json=reg_payload)
    assert reg_resp.status_code == 201
    org_id = reg_resp.json()["organization"]["id"]

    # Login with credentials
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": admin_email, "password": "Password123!"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    assert login_resp.json()["organization_id"] == org_id

    # Query /auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == admin_email
    assert me_data["active_organization_id"] == org_id
    assert me_data["active_organization_name"] == f"Nile Legal Advisory {suffix}"
    assert len(me_data["organizations"]) >= 1


def test_switch_organization_security(client: TestClient, db_session: Session):
    suffix_a = uuid.uuid4().hex[:6]
    suffix_b = uuid.uuid4().hex[:6]
    # Register Org A
    resp_a = client.post(
        "/api/v1/auth/register-organization",
        json={
            "company_name": f"Company Alpha {suffix_a}",
            "admin_email": f"alpha_{suffix_a}@test.com",
            "admin_full_name": "Alpha Admin",
            "password": "Password123!",
            "domain": "legal",
        },
    )
    assert resp_a.status_code == 201, resp_a.text
    token_a = resp_a.json()["access_token"]
    user_id = resp_a.json()["user"]["id"]
    org_a_id = resp_a.json()["organization"]["id"]

    # Register Org B with different user
    resp_b = client.post(
        "/api/v1/auth/register-organization",
        json={
            "company_name": f"Company Beta {suffix_b}",
            "admin_email": f"beta_{suffix_b}@test.com",
            "admin_full_name": "Beta Admin",
            "password": "Password123!",
            "domain": "legal",
        },
    )
    assert resp_b.status_code == 201, resp_b.text
    org_b_id = resp_b.json()["organization"]["id"]

    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Attempt to switch to Org B without membership -> 403 Forbidden
    switch_fail = client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": org_b_id},
        headers=headers_a,
    )
    assert switch_fail.status_code == 403
    err_msg = switch_fail.json().get("error", {}).get("message") or switch_fail.json().get("detail", "")
    assert "not an authorized member" in err_msg.lower()

    # Add user_a as member to Org B
    mem_b = OrganizationMembership(
        organization_id=org_b_id,
        user_id=uuid.UUID(user_id),
        role="employee",
        is_active=True,
    )
    db_session.add(mem_b)
    db_session.commit()

    # Now switch to Org B succeeds
    switch_success = client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": org_b_id},
        headers=headers_a,
    )
    assert switch_success.status_code == 200
    token_b = switch_success.json()["access_token"]
    payload_b = decode_access_token(token_b)
    assert payload_b["org_id"] == org_b_id
    assert payload_b["role"] == "employee"


def test_organization_member_management(client: TestClient):
    suffix = uuid.uuid4().hex[:6]
    admin_email = f"admin_{suffix}@deltachambers.com"
    employee_email = f"employee_{suffix}@deltachambers.com"
    # Register Org
    reg_resp = client.post(
        "/api/v1/auth/register-organization",
        json={
            "company_name": f"Delta Chambers {suffix}",
            "admin_email": admin_email,
            "admin_full_name": "Delta Admin",
            "password": "Password123!",
            "domain": "legal",
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add employee
    add_resp = client.post(
        "/api/v1/organizations/members",
        json={
            "email": employee_email,
            "full_name": "Omar Employee",
            "password": "EmployeePassword123!",
            "role": "employee",
        },
        headers=headers,
    )
    assert add_resp.status_code == 201
    assert add_resp.json()["email"] == employee_email
    assert add_resp.json()["role"] == "employee"

    # List members
    list_resp = client.get("/api/v1/organizations/members", headers=headers)
    assert list_resp.status_code == 200
    emails = [m["email"] for m in list_resp.json()]
    assert admin_email in emails
    assert employee_email in emails
