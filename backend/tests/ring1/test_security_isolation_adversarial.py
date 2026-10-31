"""Adversarial security regression tests for Ring 1 memory and context isolation.

Tests strictly verify:
1. Missing context reference rejects operations.
2. Malformed / empty / whitespace context identifiers reject operations.
3. Cross-case and cross-organization retrieval refusals.
4. Caller-supplied payload ID spoofing prevention (payload case_id / org_id tampering).
5. Sanitized error messages that do not reveal whether unauthorized records exist.
6. Indirect delegation and replanning cannot bypass context boundaries.
7. Both database-backed and in-memory paths enforce identical rules.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.ring1.contracts.capabilities import (
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    PLANNING_CREATE_PLAN,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import ReplanReasonCode
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine


@pytest.fixture
def auth_ctx_org_a_case_1() -> ContextRef:
    return ContextRef(
        organization_id="org-cairo-law",
        case_id="case-101-civil",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.fixture
def auth_ctx_org_a_case_2() -> ContextRef:
    return ContextRef(
        organization_id="org-cairo-law",
        case_id="case-102-estate",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.fixture
def auth_ctx_org_b_case_1() -> ContextRef:
    return ContextRef(
        organization_id="org-alexandria-law",
        case_id="case-101-civil",  # same case_id string, but different organization!
        status=ResolutionStatus.EXPLICIT,
    )


# ---------------------------------------------------------------------------
# 1. Missing and Empty / Malformed Contexts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("empty_val", [None, "", "   "])
async def test_memory_store_rejects_missing_or_empty_context_fields(fake_llm_service, empty_val):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # Empty case_id in ContextRef
    ctx = ContextRef(
        organization_id="org-cairo-law",
        case_id=empty_val,
        status=ResolutionStatus.EXPLICIT,
    )
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx,
        payload={"record_type": "fact", "payload": {"text": "Confidential"}},
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # Empty organization_id in ContextRef
    ctx_no_org = ContextRef(
        organization_id=empty_val,
        case_id="case-101",
        status=ResolutionStatus.EXPLICIT,
    )
    req_no_org = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_no_org,
        payload={"record_type": "fact", "payload": {"text": "Confidential"}},
    )
    resp_no_org = await engine.handle_store_record(req_no_org)
    assert resp_no_org.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp_no_org.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


@pytest.mark.asyncio
async def test_retrieval_query_rejects_missing_context(fake_llm_service):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=None,
        payload={"query": "test"},
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


# ---------------------------------------------------------------------------
# 2. Payload Spoofing Prevention (Caller tries to override authorized scope)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_memory_store_rejects_payload_case_id_spoofing(fake_llm_service, auth_ctx_org_a_case_1):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=auth_ctx_org_a_case_1,  # Authorized for case-101-civil
        payload={
            "record_type": "fact",
            "case_id": "case-victim-999",  # Attacker tries to inject into victim's case
            "payload": {"injected": "malicious_fact"},
        },
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
    assert "payload case_id does not match" in resp.errors[0].message


@pytest.mark.asyncio
async def test_memory_store_rejects_payload_org_id_spoofing(fake_llm_service, auth_ctx_org_a_case_1):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=auth_ctx_org_a_case_1,  # Authorized for org-cairo-law
        payload={
            "record_type": "fact",
            "organization_id": "org-foreign-tenant",  # Attacker tries to inject into foreign org
            "payload": {"injected": "malicious_fact"},
        },
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
    assert "payload organization_id does not match" in resp.errors[0].message


@pytest.mark.asyncio
async def test_retrieval_query_rejects_payload_case_id_spoofing(fake_llm_service, auth_ctx_org_a_case_1):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=auth_ctx_org_a_case_1,
        payload={
            "query": "confidential",
            "case_id": "case-victim-999",  # Attacker tries to query victim's case
        },
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_retrieval_query_rejects_payload_org_id_spoofing(fake_llm_service, auth_ctx_org_a_case_1):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=auth_ctx_org_a_case_1,
        payload={
            "query": "confidential",
            "organization_id": "org-victim-firm",  # Attacker tries to query victim's firm
        },
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


# ---------------------------------------------------------------------------
# 3. Cross-Tenant and Cross-Case Read Isolation & Existence Oracle Prevention
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_sanitized_error_does_not_reveal_unauthorized_record_existence(
    fake_llm_service,
    auth_ctx_org_a_case_1,
    auth_ctx_org_a_case_2,
):
    """Proves that querying an existing record from another case produces the exact same

    error code and message as querying a non-existent UUID, preventing record existence enumeration.
    """
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # Store a confidential record in case 1
    store_resp = await engine.handle_store_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_STORE_RECORD,
            context_ref=auth_ctx_org_a_case_1,
            payload={"record_type": "settlement", "payload": {"amount": 1000000}},
        )
    )
    real_rec_id = store_resp.payload["record_id"]

    # Attacker in case 2 queries the real record ID
    cross_case_resp = await engine.handle_get_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=auth_ctx_org_a_case_2,
            payload={"record_id": real_rec_id},
        )
    )

    # Attacker in case 2 queries a completely fictional non-existent record ID
    fictional_rec_id = "00000000-0000-0000-0000-000000000000"
    non_existent_resp = await engine.handle_get_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=auth_ctx_org_a_case_2,
            payload={"record_id": fictional_rec_id},
        )
    )

    # Both MUST return the identical status, error code, and sanitized error message
    assert cross_case_resp.status == ResultStatus.FAILED
    assert non_existent_resp.status == ResultStatus.FAILED
    assert cross_case_resp.errors[0].code == non_existent_resp.errors[0].code
    assert cross_case_resp.errors[0].message == non_existent_resp.errors[0].message
    assert "Access denied: unauthorized context or record does not exist." in cross_case_resp.errors[0].message


@pytest.mark.asyncio
async def test_cross_organization_same_case_id_isolation(
    fake_llm_service,
    auth_ctx_org_a_case_1,
    auth_ctx_org_b_case_1,
):
    """Case IDs might collide across different law firms (e.g. 'case-101-civil').

    Proves that organization isolation strictly prevents Org B from accessing Org A's record,
    even when case_id matches.
    """
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # Org A stores record
    store_resp = await engine.handle_store_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_STORE_RECORD,
            context_ref=auth_ctx_org_a_case_1,
            payload={"record_type": "confidential", "payload": {"client": "Org A Client"}},
        )
    )
    rec_id = store_resp.payload["record_id"]

    # Org B (same case_id, different org) tries to access
    hack_resp = await engine.handle_get_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=auth_ctx_org_b_case_1,
            payload={"record_id": rec_id},
        )
    )
    assert hack_resp.status == ResultStatus.FAILED
    assert hack_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_database_backed_cross_organization_isolation(
    db_session: Session,
    fake_llm_service,
    auth_ctx_org_a_case_1,
    auth_ctx_org_b_case_1,
):
    """Database-backed test proving PostgreSQL queries enforce both case_id and organization_id."""
    session_factory = lambda: db_session
    memory = BasicMemoryEngine(llm_service=fake_llm_service, db_session_factory=session_factory)
    retrieval = BasicRetrievalEngine(llm_service=fake_llm_service, db_session_factory=session_factory)

    # Org A stores record
    store_resp = await memory.handle_store_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_STORE_RECORD,
            context_ref=auth_ctx_org_a_case_1,
            payload={"record_type": "evidence", "payload": {"document": "Secret Contract"}},
        )
    )
    rec_id = store_resp.payload["record_id"]

    # Org B tries GET
    get_resp = await memory.handle_get_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=auth_ctx_org_b_case_1,
            payload={"record_id": rec_id},
        )
    )
    assert get_resp.status == ResultStatus.FAILED
    assert get_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value

    # Org B queries retrieval — must return 0 results
    query_resp = await retrieval.handle_query(
        MeshRequest(
            sender_engine="client",
            recipient_capability=RETRIEVAL_QUERY,
            context_ref=auth_ctx_org_b_case_1,
            payload={"query": "Secret Contract"},
        )
    )
    assert query_resp.status == ResultStatus.SUCCESS
    assert len(query_resp.payload["records"]) == 0


# ---------------------------------------------------------------------------
# 4. Indirect Delegation and Replanning Cannot Bypass Scope
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_replanning_cannot_inject_unauthorized_cross_case_context(
    fake_llm_service,
    auth_ctx_org_a_case_1,
    auth_ctx_org_a_case_2,
):
    """Proves that requesting a replan cannot be exploited to widen scope or access another case."""
    planning = PlanningEngine(llm_service=fake_llm_service)

    # Create plan in Case 1
    create_resp = await planning.handle_create_plan(
        MeshRequest(
            sender_engine="client",
            recipient_capability=PLANNING_CREATE_PLAN,
            context_ref=auth_ctx_org_a_case_1,
            payload={"goal": "Process confidential case 1 evidence"},
        )
    )
    plan_id = create_resp.payload["plan_id"]
    failed_step_id = create_resp.payload["steps"][0]["step_id"]

    # Replan request carries Case 1 context_ref
    replan_resp = await planning.handle_request_replan(
        MeshRequest(
            sender_engine="plan_executor",
            recipient_capability=PLANNING_REQUEST_REPLAN,
            context_ref=auth_ctx_org_a_case_1,
            payload={
                "plan_id": plan_id,
                "failed_step_id": failed_step_id,
                "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
                "evidence": {"attempted_case": "case-102-estate"},
            },
        )
    )
    assert replan_resp.status == ResultStatus.SUCCESS

    # Revised plan preserves original Case 1 context boundary
    revised_plan = planning._plans[plan_id]
    assert revised_plan.context_ref == auth_ctx_org_a_case_1.ref
