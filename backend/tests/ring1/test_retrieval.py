"""Tests for Basic Retrieval Engine."""

import pytest

from app.ring1.contracts.capabilities import RETRIEVAL_QUERY
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.retrieval import BasicRetrievalEngine


@pytest.fixture
def ctx_ref() -> ContextRef:
    return ContextRef(
        organization_id="org-test",
        case_id="case-abc",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.mark.asyncio
async def test_retrieval_query_in_memory(fake_llm_service, ctx_ref):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)

    # Add records to retrieval engine
    engine.add_in_memory_record({
        "record_id": "rec-1",
        "case_id": "case-abc",
        "record_type": "contract_clause",
        "payload": {"text": "Confidentiality clause binds both parties"},
    })
    engine.add_in_memory_record({
        "record_id": "rec-2",
        "case_id": "case-abc",
        "record_type": "memo",
        "payload": {"text": "Billing rate summary"},
    })
    # Foreign record from another case
    engine.add_in_memory_record({
        "record_id": "rec-3",
        "case_id": "case-FOREIGN",
        "record_type": "contract_clause",
        "payload": {"text": "Confidentiality clause from foreign client"},
    })

    # Query within case-abc
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_ref,
        payload={"query": "Confidentiality"},
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.SUCCESS
    records = resp.payload["records"]
    assert len(records) == 1
    assert records[0]["record_id"] == "rec-1"
    assert records[0]["case_id"] == "case-abc"


@pytest.mark.asyncio
async def test_retrieval_missing_case_id(fake_llm_service):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)
    ctx_without_case = ContextRef(
        organization_id="org-test",
        case_id=None,
        status=ResolutionStatus.UNRESOLVED,
    )
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_without_case,
        payload={"query": "anything"},
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


@pytest.mark.asyncio
async def test_retrieval_record_type_filter(fake_llm_service, ctx_ref):
    engine = BasicRetrievalEngine(llm_service=fake_llm_service)
    engine.add_in_memory_record({
        "record_id": "rec-10",
        "case_id": "case-abc",
        "record_type": "type_a",
        "payload": {"info": "match"},
    })
    engine.add_in_memory_record({
        "record_id": "rec-11",
        "case_id": "case-abc",
        "record_type": "type_b",
        "payload": {"info": "match"},
    })

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_ref,
        payload={"record_type": "type_a"},
    )
    resp = await engine.handle_query(req)
    assert resp.status == ResultStatus.SUCCESS
    assert len(resp.payload["records"]) == 1
    assert resp.payload["records"][0]["record_id"] == "rec-10"
