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


# ---------------------------------------------------------------------------
# P0 Regression — handle_get_record must require context_ref
# (audit finding: unscoped GET allowed cross-case read when context_ref=None)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_memory_get_requires_context_ref(fake_llm_service, ctx_ref):
    """A GET with no context_ref must be rejected with CONTEXT_MISSING.

    Before the fix, missing context_ref caused expected_case_id=None which
    bypassed the isolation guard and allowed any record to be fetched.
    """
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # First store a record with a valid context (case-100)
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability="memory.store_record",
        context_ref=ctx_ref,
        payload={
            "record_type": "secret",
            "payload": {"secret": "classified"},
        },
    )
    store_resp = await engine.handle_store_record(store_req)
    assert store_resp.status == ResultStatus.SUCCESS
    rec_id = store_resp.payload["record_id"]

    # Now attempt to GET with no context_ref — must be blocked
    no_ctx_req = MeshRequest(
        sender_engine="attacker",
        recipient_capability="memory.get_record",
        context_ref=None,  # no context
        payload={"record_id": rec_id},
    )
    no_ctx_resp = await engine.handle_get_record(no_ctx_req)
    assert no_ctx_resp.status == ResultStatus.NEEDS_CLARIFICATION, (
        f"Expected NEEDS_CLARIFICATION but got {no_ctx_resp.status}. "
        "The P0 security fix (require_context_ref on GET) may have been reverted."
    )
    assert no_ctx_resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


@pytest.mark.asyncio
async def test_memory_cross_organization_isolation(fake_llm_service, ctx_ref):
    """A record stored under org-A must not be retrievable by org-B, even with same case_id."""
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,  # org-test, case-100
        payload={"record_type": "note", "payload": {"data": "confidential_org_data"}},
    )
    store_resp = await engine.handle_store_record(store_req)
    assert store_resp.status == ResultStatus.SUCCESS
    rec_id = store_resp.payload["record_id"]

    # Request from different org
    ctx_other_org = ContextRef(
        organization_id="org-foreign",
        case_id="case-100",
        status=ResolutionStatus.EXPLICIT,
    )
    get_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_other_org,
        payload={"record_id": rec_id},
    )
    get_resp = await engine.handle_get_record(get_req)
    assert get_resp.status == ResultStatus.FAILED
    assert get_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_memory_get_requires_case_id_and_org_id_in_context(fake_llm_service):
    """ContextRef without case_id or without organization_id must be rejected."""
    engine = BasicMemoryEngine(llm_service=fake_llm_service)

    # Missing case_id
    ctx_no_case = ContextRef(
        organization_id="org-test",
        case_id=None,
        status=ResolutionStatus.INSUFFICIENT_DATA,
    )
    req1 = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_no_case,
        payload={"record_id": "dummy-id"},
    )
    resp1 = await engine.handle_get_record(req1)
    assert resp1.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp1.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # Missing organization_id
    ctx_no_org = ContextRef(
        organization_id=None,
        case_id="case-100",
        status=ResolutionStatus.INSUFFICIENT_DATA,
    )
    req2 = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_no_org,
        payload={"record_id": "dummy-id"},
    )
    resp2 = await engine.handle_get_record(req2)
    assert resp2.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp2.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value


@pytest.mark.asyncio
async def test_memory_payload_case_id_spoofing_rejected(fake_llm_service, ctx_ref):
    """If payload case_id conflicts with context_ref.case_id, request is denied."""
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_ref,  # case-100
        payload={"record_id": "some-id", "case_id": "case-spoofed"},
    )
    resp = await engine.handle_get_record(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_memory_error_messages_do_not_leak_sensitive_info(fake_llm_service, ctx_ref):
    """Denial and not-found error messages must not leak existence or foreign case identifiers."""
    engine = BasicMemoryEngine(llm_service=fake_llm_service)
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,  # org-test, case-100
        payload={"record_type": "secret", "payload": {"privileged": "classified_info"}},
    )
    store_resp = await engine.handle_store_record(store_req)
    rec_id = store_resp.payload["record_id"]

    # Foreign context
    foreign_ctx = ContextRef(
        organization_id="org-foreign",
        case_id="case-999",
        status=ResolutionStatus.EXPLICIT,
    )
    denied_req = MeshRequest(
        sender_engine="attacker",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=foreign_ctx,
        payload={"record_id": rec_id},
    )
    denied_resp = await engine.handle_get_record(denied_req)
    assert denied_resp.status == ResultStatus.FAILED
    assert denied_resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
    err_msg = denied_resp.errors[0].message
    assert "case-100" not in err_msg, "Error message leaked actual case_id"
    assert "org-test" not in err_msg, "Error message leaked actual organization_id"
    assert "classified_info" not in err_msg, "Error message leaked secret payload"


@pytest.mark.asyncio
async def test_memory_db_path_unauthorized_access_rejected(fake_llm_service, db_session, ctx_ref):
    """Database-backed path strictly rejects cross-case, cross-org, and unscoped reads."""
    engine = BasicMemoryEngine(llm_service=fake_llm_service, db_session_factory=lambda: db_session)

    # 1. Store record in DB
    store_req = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref,
        payload={"record_type": "db_secret", "payload": {"db_key": "val_123"}},
    )
    store_resp = await engine.handle_store_record(store_req)
    assert store_resp.status == ResultStatus.SUCCESS
    rec_id = store_resp.payload["record_id"]

    # 2. Legitimate read works
    get_ok = await engine.handle_get_record(
        MeshRequest(
            sender_engine="client",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=ctx_ref,
            payload={"record_id": rec_id},
        )
    )
    assert get_ok.status == ResultStatus.SUCCESS
    assert get_ok.payload["payload"]["db_key"] == "val_123"

    # 3. Cross-case read rejected in DB path
    foreign_case_ctx = ContextRef(
        organization_id="org-test",
        case_id="case-foreign",
        status=ResolutionStatus.EXPLICIT,
    )
    get_fail_case = await engine.handle_get_record(
        MeshRequest(
            sender_engine="attacker",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=foreign_case_ctx,
            payload={"record_id": rec_id},
        )
    )
    assert get_fail_case.status == ResultStatus.FAILED
    assert get_fail_case.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
    assert "case-100" not in get_fail_case.errors[0].message

    # 4. Cross-org read rejected in DB path
    foreign_org_ctx = ContextRef(
        organization_id="org-other",
        case_id="case-100",
        status=ResolutionStatus.EXPLICIT,
    )
    get_fail_org = await engine.handle_get_record(
        MeshRequest(
            sender_engine="attacker",
            recipient_capability=MEMORY_GET_RECORD,
            context_ref=foreign_org_ctx,
            payload={"record_id": rec_id},
        )
    )
    assert get_fail_org.status == ResultStatus.FAILED
    assert get_fail_org.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value
