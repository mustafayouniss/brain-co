"""Tests for strict context and case isolation in Ring 1."""

import pytest
from sqlalchemy.orm import Session

from app.ring1.contracts.capabilities import (
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    RETRIEVAL_QUERY,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine


@pytest.fixture
def ctx_case_a() -> ContextRef:
    return ContextRef(
        organization_id="org-acme",
        case_id="case-AAA",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.fixture
def ctx_case_b() -> ContextRef:
    return ContextRef(
        organization_id="org-acme",
        case_id="case-BBB",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.mark.asyncio
async def test_cross_case_isolation_in_memory(fake_llm_service, ctx_case_a, ctx_case_b):
    memory = BasicMemoryEngine(llm_service=fake_llm_service)
    retrieval = BasicRetrievalEngine(llm_service=fake_llm_service, memory_engine=memory)

    # 1. Store confidential record in Case A
    store_a_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_case_a,
        payload={
            "record_type": "settlement_offer",
            "payload": {"amount": 500000, "confidential": True},
        },
    )
    store_a_resp = await memory.handle_store_record(store_a_req)
    rec_a_id = store_a_resp.payload["record_id"]

    # 2. Store normal record in Case B
    store_b_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_case_b,
        payload={
            "record_type": "settlement_offer",
            "payload": {"amount": 10000, "confidential": False},
        },
    )
    store_b_resp = await memory.handle_store_record(store_b_req)
    rec_b_id = store_b_resp.payload["record_id"]

    # 3. Query from Case B context — MUST NOT see Case A settlement offer
    query_b_req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_case_b,
        payload={"query": "settlement"},
    )
    query_b_resp = await retrieval.handle_query(query_b_req)
    assert query_b_resp.status == ResultStatus.SUCCESS
    returned_records = query_b_resp.payload["records"]
    assert len(returned_records) == 1
    assert returned_records[0]["record_id"] == rec_b_id
    assert returned_records[0]["case_id"] == "case-BBB"

    # 4. Direct GET from Case B requesting Case A record — MUST FAIL
    get_hack_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_case_b,
        payload={"record_id": rec_a_id},
    )
    get_hack_resp = await memory.handle_get_record(get_hack_req)
    assert get_hack_resp.status == ResultStatus.FAILED
    assert get_hack_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_cross_case_isolation_in_db(db_session: Session, fake_llm_service, ctx_case_a, ctx_case_b):
    """Database-backed test using real PostgreSQL test container via db_session fixture."""
    # Session factory returning the transactional test session
    session_factory = lambda: db_session

    memory = BasicMemoryEngine(llm_service=fake_llm_service, db_session_factory=session_factory)
    retrieval = BasicRetrievalEngine(llm_service=fake_llm_service, db_session_factory=session_factory)

    # 1. Store confidential record in Case A
    store_a_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_case_a,
        payload={
            "record_type": "privileged_evidence",
            "payload": {"details": "Deposition transcript of witness"},
        },
    )
    store_a_resp = await memory.handle_store_record(store_a_req)
    assert store_a_resp.status == ResultStatus.SUCCESS
    rec_a_id = store_a_resp.payload["record_id"]

    # 2. Store record in Case B
    store_b_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_case_b,
        payload={
            "record_type": "public_filing",
            "payload": {"details": "Public notice"},
        },
    )
    store_b_resp = await memory.handle_store_record(store_b_req)
    assert store_b_resp.status == ResultStatus.SUCCESS
    rec_b_id = store_b_resp.payload["record_id"]

    # 3. Query from Case B context — MUST NOT see Case A evidence
    query_b_req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_case_b,
        payload={"query": "evidence"},
    )
    query_b_resp = await retrieval.handle_query(query_b_req)
    assert query_b_resp.status == ResultStatus.SUCCESS
    assert len(query_b_resp.payload["records"]) == 0  # No "evidence" in Case B

    # 4. Direct GET from Case B for Case A record — MUST FAIL
    get_hack_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_case_b,
        payload={"record_id": rec_a_id},
    )
    get_hack_resp = await memory.handle_get_record(get_hack_req)
    assert get_hack_resp.status == ResultStatus.FAILED
    assert get_hack_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
