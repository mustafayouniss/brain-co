"""Adversarial and lifecycle security tests for SEC-05: Memory Validation Authority Lifecycle.

Verifies:
1. Untrusted mesh requests (without validation authority) store records strictly as 'candidate'.
2. Client/peer payload cannot forge 'validation_authority' or self-promote to 'active'/'validated'.
3. Only context with verified validation_authority=True can store records directly as validated.
4. Non-admin / unauthorized actor cannot promote or reject candidate records.
5. Authorized validation authority promotes candidate to 'validated' with provenance audit trail.
6. Unvalidated candidate records are excluded from standard retrieval searches.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from brain.general.contracts.capabilities import MEMORY_STORE_RECORD, MEMORY_GET_RECORD
from brain.general.contracts.context import BrainContext
from brain.general.contracts.context_ref import ContextRef, ResolutionStatus
from brain.general.contracts.envelopes import MeshRequest, ResultStatus
from brain.general.contracts.errors import EngineErrorCode
from brain.general.engines.memory import BasicMemoryEngine
from brain.general.stores.in_memory_memory import InMemoryMemoryStore
from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.ring1.models.observation import MemoryRecord


@pytest.fixture
def standard_user(db_session: Session) -> User:
    user = User(
        email=f"employee_{uuid.uuid4().hex[:8]}@example.com",
        full_name="Standard Employee",
        hashed_password=hash_password("password123"),
        role="employee",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def admin_user(db_session: Session) -> User:
    user = User(
        email=f"admin_{uuid.uuid4().hex[:8]}@example.com",
        full_name="System Admin",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def standard_headers(standard_user: User) -> dict[str, str]:
    token = create_access_token(str(standard_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(admin_user: User) -> dict[str, str]:
    token = create_access_token(str(admin_user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_untrusted_mesh_request_stores_as_candidate():
    """SEC-05: Untrusted Mesh requests must store records as 'candidate', not 'active'."""
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(
            organization_id="org-acme",
            case_id="case-100",
            validation_authority=False,  # No validation authority
        ),
        payload={
            "payload": {"fact": "Unverified legal proposition"},
            "status": "active",  # Adversarial attempt to self-promote
            "record_type": "legal_fact",
        },
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["status"] == "candidate"

    rec_id = resp.payload["record_id"]
    stored_rec = await store.get_record(rec_id, organization_id="org-acme", case_id="case-100")
    assert stored_rec is not None
    assert stored_rec["status"] == "candidate"


@pytest.mark.asyncio
async def test_trusted_validation_authority_can_store_as_validated():
    """SEC-05: Context with verified validation_authority=True can store directly as validated."""
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    req = MeshRequest(
        sender_engine="admin",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(
            organization_id="org-acme",
            case_id="case-100",
            validation_authority=True,  # Verified validation authority
        ),
        payload={
            "payload": {"fact": "Authoritative court ruling"},
            "status": "validated",
            "record_type": "court_ruling",
        },
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["status"] == "validated"

    rec_id = resp.payload["record_id"]
    stored_rec = await store.get_record(rec_id, organization_id="org-acme", case_id="case-100")
    assert stored_rec is not None
    assert stored_rec["status"] == "validated"


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_promote_candidate():
    """SEC-05: Non-admin without validation authority cannot validate candidates."""
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    # 1. Ingest candidate
    ingest_ctx = BrainContext(
        organization_id="org-acme",
        case_id="case-100",
        role="employee",
        validation_authority=False,
    )
    ingest_res = await engine.store_candidate(
        fact_data={"fact": "Witness testimony", "record_type": "testimony"},
        context=ingest_ctx,
    )
    rec_id = ingest_res.data["record_id"]
    assert ingest_res.data["status"] == "candidate"

    # 2. Unauthorized attempt to promote
    unauthorized_ctx = BrainContext(
        organization_id="org-acme",
        case_id="case-100",
        role="employee",
        validation_authority=False,
    )
    promote_res = await engine.validate_candidate(
        record_id=rec_id,
        action="VALIDATE",
        context=unauthorized_ctx,
    )
    assert promote_res.error is not None
    assert promote_res.error["code"] == "VALIDATION_AUTHORITY_REQUIRED"

    # Status must remain candidate
    check_rec = await store.get_record(rec_id, organization_id="org-acme", case_id="case-100")
    assert check_rec["status"] == "candidate"


@pytest.mark.asyncio
async def test_authorized_admin_promotes_candidate_to_validated():
    """SEC-05: Validation authority promotes candidate to 'validated' with audit metadata."""
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    # 1. Ingest candidate
    ingest_ctx = BrainContext(
        organization_id="org-acme",
        case_id="case-100",
        role="employee",
        validation_authority=False,
    )
    ingest_res = await engine.store_candidate(
        fact_data={"fact": "Contract terms", "record_type": "contract"},
        context=ingest_ctx,
    )
    rec_id = ingest_res.data["record_id"]

    # 2. Authorized promotion
    admin_ctx = BrainContext(
        organization_id="org-acme",
        case_id="case-100",
        user_id="admin-user-001",
        role="admin",
        validation_authority=True,
    )
    promote_res = await engine.validate_candidate(
        record_id=rec_id,
        action="VALIDATE",
        context=admin_ctx,
    )
    assert promote_res.error is None
    assert promote_res.data["status"] == "validated"
    assert promote_res.data["metadata"]["validated_by"] == "admin-user-001"

    # Record in store is now validated
    check_rec = await store.get_record(rec_id, organization_id="org-acme", case_id="case-100")
    assert check_rec["status"] == "validated"


def test_retrieval_excludes_unvalidated_candidates(
    client: TestClient,
    db_session: Session,
    standard_headers: dict[str, str],
    admin_headers: dict[str, str],
):
    """SEC-05: Retrieval endpoint excludes candidates from standard searches."""
    case_id = f"case-mem-{uuid.uuid4().hex[:8]}"
    org_id = "org-brain-corp"

    # 1. Create a candidate record
    cand = MemoryRecord(
        id=uuid.uuid4(),
        record_type="preliminary_claim",
        case_id=case_id,
        organization_id=org_id,
        payload={"claim": "Confidential settlement proposition keyword_unvalidated_secret"},
        status="candidate",  # Candidate, not validated!
    )
    # 2. Create a validated record
    val = MemoryRecord(
        id=uuid.uuid4(),
        record_type="binding_verdict",
        case_id=case_id,
        organization_id=org_id,
        payload={"claim": "Official court judgment keyword_unvalidated_secret"},
        status="validated",
    )
    db_session.add_all([cand, val])
    db_session.commit()

    # 3. Standard employee search: MUST only return the validated record
    res_emp = client.get(
        "/api/v1/retrieval/search",
        params={"q": "keyword_unvalidated_secret"},
        headers={**standard_headers, "X-Case-ID": case_id},
    )
    assert res_emp.status_code == 200
    emp_data = res_emp.json()
    assert emp_data["total_found"] == 1
    assert emp_data["items"][0]["record_id"] == str(val.id)

    # 4. Admin search with include_candidates=True: returns both
    res_adm = client.get(
        "/api/v1/retrieval/search",
        params={"q": "keyword_unvalidated_secret", "include_candidates": True},
        headers={**admin_headers, "X-Case-ID": case_id},
    )
    assert res_adm.status_code == 200
    adm_data = res_adm.json()
    assert adm_data["total_found"] == 2
