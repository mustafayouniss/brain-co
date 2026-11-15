"""Comprehensive Multi-Tenant SaaS Isolation Test Suite.

Proves tenant boundary enforcement across 5 real organizations:
1. Cairo Legal Partners
2. Alexandria Law Chambers
3. Nile Dispute Resolution
4. Giza Corporate Counsel
5. Red Sea Legal Advisory

Verifies:
- Distinct tenant database identities & JWT tokens
- Case partitioned listing and access control
- Cross-tenant ID forgery and direct case lookup defense (404/403)
- Unauthorized organization switching defense (403)
- Case memory record isolation in PostgreSQL
- AI Employee grounded context authorization barrier
- Member list tenant scoping
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.models.case import Case
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.ring1.models.observation import MemoryRecord


ORGANIZATION_SPECS = [
    {
        "company_name": "Cairo Legal Partners",
        "email_prefix": "cairo_admin",
        "admin_name": "Tarek Mansour",
        "case_number": "CLP-2026-001",
        "case_title": "Cairo Commercial Merger",
    },
    {
        "company_name": "Alexandria Law Chambers",
        "email_prefix": "alex_admin",
        "admin_name": "Samir Amin",
        "case_number": "ALC-2026-002",
        "case_title": "Alexandria Maritime Charter Dispute",
    },
    {
        "company_name": "Nile Dispute Resolution",
        "email_prefix": "nile_admin",
        "admin_name": "Mona El-Sayed",
        "case_number": "NDR-2026-003",
        "case_title": "Nile Basin Engineering Arbitration",
    },
    {
        "company_name": "Giza Corporate Counsel",
        "email_prefix": "giza_admin",
        "admin_name": "Khaled Fahmy",
        "case_number": "GCC-2026-004",
        "case_title": "Giza Real Estate Development Compliance",
    },
    {
        "company_name": "Red Sea Legal Advisory",
        "email_prefix": "redsea_admin",
        "admin_name": "Hoda Youssef",
        "case_number": "RSLA-2026-005",
        "case_title": "Red Sea Renewable Energy Concession",
    },
]


def test_five_real_organizations_signup_and_isolation(client: TestClient, db_session: Session):
    """Register all 5 organizations, establish distinct identities, and verify complete isolation."""
    run_suffix = uuid.uuid4().hex[:6]
    registered_orgs = []

    # 1. Register each organization via the SaaS Signup endpoint
    for spec in ORGANIZATION_SPECS:
        admin_email = f"{spec['email_prefix']}_{run_suffix}@lawfirm.eg"
        payload = {
            "company_name": f"{spec['company_name']} {run_suffix}",
            "admin_email": admin_email,
            "admin_full_name": spec["admin_name"],
            "password": "SecurePassword123!",
            "domain": "legal",
        }
        resp = client.post("/api/v1/auth/register-organization", json=payload)
        assert resp.status_code == 201, resp.text
        data = resp.json()

        org_id = data["organization"]["id"]
        token = data["access_token"]
        claims = decode_access_token(token)

        assert claims["org_id"] == org_id
        assert claims["role"] == "admin"
        assert claims["domain"] == "legal"

        registered_orgs.append({
            **spec,
            "org_id": org_id,
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "user_id": data["user"]["id"],
            "admin_email": admin_email,
        })

    # Verify that all 5 organizations have unique IDs
    org_ids = [org["org_id"] for org in registered_orgs]
    assert len(set(org_ids)) == 5

    # 2. Each organization creates its own legal case
    for org in registered_orgs:
        case_resp = client.post(
            "/api/v1/cases",
            json={
                "case_number": f"{org['case_number']}-{run_suffix}",
                "title": org["case_title"],
                "description": f"Confidential case file for {org['company_name']}",
            },
            headers=org["headers"],
        )
        assert case_resp.status_code == 201, case_resp.text
        org["case_id"] = case_resp.json()["id"]

    # 3. Verify strict case listing isolation:
    # Each org must only see its own case, never other organizations' cases.
    for i, org in enumerate(registered_orgs):
        list_resp = client.get("/api/v1/cases", headers=org["headers"])
        assert list_resp.status_code == 200
        case_items = list_resp.json()
        case_numbers = [c["case_number"] for c in case_items]

        # Own case must be present
        assert f"{org['case_number']}-{run_suffix}" in case_numbers

        # Other organizations' cases must NEVER be present
        for j, other_org in enumerate(registered_orgs):
            if i != j:
                assert f"{other_org['case_number']}-{run_suffix}" not in case_numbers

    # 4. Verify direct case ID cross-tenant lookup defense:
    # Org 1 attempting to GET Org 2's case ID must receive 404 NOT FOUND.
    org1 = registered_orgs[0]
    org2 = registered_orgs[1]
    cross_lookup = client.get(f"/api/v1/cases/{org2['case_id']}", headers=org1["headers"])
    assert cross_lookup.status_code == 404

    # 5. Verify unauthorized organization switching defense:
    # Org 1 admin attempting to switch to Org 2 must receive 403 FORBIDDEN.
    switch_attempt = client.post(
        "/api/v1/auth/switch-organization",
        json={"organization_id": org2["org_id"]},
        headers=org1["headers"],
    )
    assert switch_attempt.status_code == 403

    # 6. Verify knowledge memory isolation:
    # Insert a confidential record for Org 1's case
    mem_rec = MemoryRecord(
        id=str(uuid.uuid4()),
        organization_id=org1["org_id"],
        case_id=org1["case_id"],
        record_type="legal_obligation",
        payload={
            "facts": [
                {"statement": f"Confidential merger clause for {org1['company_name']}"}
            ]
        },
    )
    db_session.add(mem_rec)
    db_session.commit()

    # Org 1 can retrieve its memory record
    know_org1 = client.get(
        f"/api/v1/ring1/knowledge?case_id={org1['case_id']}",
        headers=org1["headers"],
    )
    assert know_org1.status_code == 200
    assert know_org1.json()["total"] >= 1

    # Org 2 attempting to query Org 1's case with forged organization_id receives 403 FORBIDDEN
    know_forged = client.get(
        f"/api/v1/ring1/knowledge?organization_id={org1['org_id']}&case_id={org1['case_id']}",
        headers=org2["headers"],
    )
    assert know_forged.status_code == 403

    # 7. Verify AI Employee context boundary defense:
    # Org 2 asking AI Employee about Org 1's case receives 403 FORBIDDEN (context fail-closed)
    ai_cross_case = client.post(
        "/api/v1/ai/prompt",
        json={
            "prompt": "What are the merger terms?",
            "context": "legal",
            "case_id": org1["case_id"],
        },
        headers=org2["headers"],
    )
    assert ai_cross_case.status_code == 403

    # Org 1 asking about its own case succeeds
    ai_own_case = client.post(
        "/api/v1/ai/prompt",
        json={
            "prompt": "Summarize case status",
            "context": "legal",
            "case_id": org1["case_id"],
        },
        headers=org1["headers"],
    )
    assert ai_own_case.status_code == 200
    assert ai_own_case.json()["content"] != ""

    # 8. Verify Member Management isolation:
    # Add an employee to Org 1
    emp_email = f"cairo_associate_{run_suffix}@cairolegal.com"
    add_mem = client.post(
        "/api/v1/organizations/members",
        json={
            "email": emp_email,
            "full_name": "Counselor Karim Nabil",
            "password": "Password123!",
            "role": "employee",
        },
        headers=org1["headers"],
    )
    assert add_mem.status_code == 201

    # Org 1 sees the new employee
    org1_members = client.get("/api/v1/organizations/members", headers=org1["headers"]).json()
    assert any(m["email"] == emp_email for m in org1_members)

    # Org 2 does NOT see Org 1's employee
    org2_members = client.get("/api/v1/organizations/members", headers=org2["headers"]).json()
    assert not any(m["email"] == emp_email for m in org2_members)
