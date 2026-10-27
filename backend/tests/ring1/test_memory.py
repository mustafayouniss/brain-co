"""Tests for Basic Memory Engine."""

import pytest

from app.ring1.contracts.capabilities import MEMORY_GET_RECORD, MEMORY_STORE_RECORD
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.memory import BasicMemoryEngine


@pytest.fixture
def ctx_ref() -> ContextRef:
    return ContextRef(
        organization_id="org-test",
        case_id="case-100",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.mark.asyncio
async def test_memory_store_and_get(fake_llm_service, ctx_ref):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # Store
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,
        payload={
            "record_type": "legal_fact",
            "payload": {"claim": "Statute of limitations expired"},
            "idempotency_key": "fact-1",
        },
    )
    store_resp = await engine.handle_store_record(store_req)
    assert store_resp.status == ResultStatus.SUCCESS
    record_id = store_resp.payload["record_id"]
    assert store_resp.payload["duplicate"] is False

    # Get
    get_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_ref,
        payload={"record_id": record_id},
    )
    get_resp = await engine.handle_get_record(get_req)
    assert get_resp.status == ResultStatus.SUCCESS
    assert get_resp.payload["payload"]["claim"] == "Statute of limitations expired"
    assert get_resp.payload["case_id"] == "case-100"


@pytest.mark.asyncio
async def test_memory_store_requires_context_ref(fake_llm_service):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=None,  # Missing
        payload={"record_type": "note", "payload": {"text": "hello"}},
    )
    resp = await engine.handle_store_record(req)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


@pytest.mark.asyncio
async def test_memory_idempotency(fake_llm_service, ctx_ref):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,
        payload={
            "record_type": "event",
            "payload": {"status": "ok"},
            "idempotency_key": "unique-idemp-123",
        },
    )
    resp1 = await engine.handle_store_record(req)
    assert resp1.payload["duplicate"] is False

    resp2 = await engine.handle_store_record(req)
    assert resp2.payload["duplicate"] is True
    assert resp2.payload["record_id"] == resp1.payload["record_id"]


@pytest.mark.asyncio
async def test_memory_cross_case_isolation(fake_llm_service, ctx_ref):
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    # Store record in case-100
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,
        payload={"record_type": "secret", "payload": {"secret_key": "alpha"}},
    )
    store_resp = await engine.handle_store_record(store_req)
    rec_id = store_resp.payload["record_id"]

    # Try to access with a different case_id (case-200)
    ctx_other = ContextRef(
        organization_id="org-test",
        case_id="case-200",
        status=ResolutionStatus.EXPLICIT,
    )
    hack_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_other,
        payload={"record_id": rec_id, "case_id": "case-200"},
    )
    hack_resp = await engine.handle_get_record(hack_req)
    assert hack_resp.status == ResultStatus.FAILED
    assert hack_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
