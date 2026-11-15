"""Regression and adversarial tests for SEC-01: Tenant-scoped Idempotency Keys.

Verifies:
1. In-memory observation and memory stores isolate idempotency keys per organization.
2. SQLAlchemy observation and memory stores isolate idempotency keys per organization in PostgreSQL.
3. Engines (ObservationEngine and BasicMemoryEngine) isolate idempotency keys across organizations.
4. An adversarial tenant cannot block or inspect another tenant's records by guessing idempotency keys.
"""

from __future__ import annotations

import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from brain.general.contracts.context import BrainContext
from brain.general.contracts.envelopes import MeshRequest, ResultStatus, ContextRef
from brain.general.contracts.errors import EngineErrorCode
from brain.general.contracts.capabilities import OBSERVATION_RECORD_EVENT, MEMORY_STORE_RECORD
from brain.general.stores.in_memory_observation import InMemoryObservationStore
from brain.general.stores.in_memory_memory import InMemoryMemoryStore
from brain.general.engines.observation import ObservationEngine
from brain.general.engines.memory import BasicMemoryEngine

from app.infrastructure.database.stores import (
    SqlAlchemyObservationStore,
    SqlAlchemyMemoryStore,
)
from app.ring1.models.observation import Observation, MemoryRecord


@pytest.mark.asyncio
async def test_in_memory_observation_idempotency_tenant_isolation():
    store = InMemoryObservationStore()
    shared_key = "idemp-obs-shared-12345"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"
    org_c = f"org_{uuid.uuid4().hex[:8]}"

    rec_a = {
        "id": str(uuid.uuid4()),
        "organization_id": org_a,
        "event_type": "contract.uploaded",
        "source": "tenant_a",
        "idempotency_key": shared_key,
        "payload": {"secret_a": "confidential_a"},
    }
    rec_b = {
        "id": str(uuid.uuid4()),
        "organization_id": org_b,
        "event_type": "contract.uploaded",
        "source": "tenant_b",
        "idempotency_key": shared_key,
        "payload": {"secret_b": "confidential_b"},
    }

    await store.save(rec_a)
    await store.save(rec_b)

    found_a = await store.find_by_idempotency_key(shared_key, organization_id=org_a)
    assert found_a is not None
    assert found_a["id"] == rec_a["id"]
    assert found_a["organization_id"] == org_a
    assert found_a["payload"]["secret_a"] == "confidential_a"

    found_b = await store.find_by_idempotency_key(shared_key, organization_id=org_b)
    assert found_b is not None
    assert found_b["id"] == rec_b["id"]
    assert found_b["organization_id"] == org_b
    assert found_b["payload"]["secret_b"] == "confidential_b"

    found_c = await store.find_by_idempotency_key(shared_key, organization_id=org_c)
    assert found_c is None


@pytest.mark.asyncio
async def test_in_memory_memory_idempotency_tenant_isolation():
    store = InMemoryMemoryStore()
    shared_key = "idemp-mem-shared-99999"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"
    org_c = f"org_{uuid.uuid4().hex[:8]}"

    rec_a = {
        "id": str(uuid.uuid4()),
        "record_id": str(uuid.uuid4()),
        "organization_id": org_a,
        "case_id": "case_001",
        "fact": "Tenant A sensitive fact",
        "idempotency_key": shared_key,
        "confidence": 0.95,
        "status": "candidate",
    }
    rec_b = {
        "id": str(uuid.uuid4()),
        "record_id": str(uuid.uuid4()),
        "organization_id": org_b,
        "case_id": "case_002",
        "fact": "Tenant B sensitive fact",
        "idempotency_key": shared_key,
        "confidence": 0.85,
        "status": "candidate",
    }

    await store.save_record(rec_a)
    await store.save_record(rec_b)

    found_a = await store.find_by_idempotency_key(shared_key, organization_id=org_a)
    assert found_a is not None
    assert found_a["id"] == rec_a["id"]
    assert found_a["organization_id"] == org_a
    assert found_a["fact"] == "Tenant A sensitive fact"

    found_b = await store.find_by_idempotency_key(shared_key, organization_id=org_b)
    assert found_b is not None
    assert found_b["id"] == rec_b["id"]
    assert found_b["organization_id"] == org_b
    assert found_b["fact"] == "Tenant B sensitive fact"

    found_c = await store.find_by_idempotency_key(shared_key, organization_id=org_c)
    assert found_c is None


@pytest.mark.asyncio
async def test_observation_engine_tenant_idempotency_isolation():
    store = InMemoryObservationStore()
    engine = ObservationEngine(store=store)

    shared_key = "eng-obs-idemp-001"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"

    req_a1 = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id=org_a),
        payload={
            "event_type": "document.created",
            "source": "client_a",
            "idempotency_key": shared_key,
            "payload": {"doc": "A"},
        },
    )
    resp_a1 = await engine.handle_record_event(req_a1)
    assert resp_a1.status == ResultStatus.SUCCESS
    assert resp_a1.payload["duplicate"] is False
    obs_id_a = resp_a1.payload["observation_id"]

    req_b1 = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id=org_b),
        payload={
            "event_type": "document.created",
            "source": "client_b",
            "idempotency_key": shared_key,
            "payload": {"doc": "B"},
        },
    )
    resp_b1 = await engine.handle_record_event(req_b1)
    assert resp_b1.status == ResultStatus.SUCCESS
    assert resp_b1.payload["duplicate"] is False
    obs_id_b = resp_b1.payload["observation_id"]
    assert obs_id_a != obs_id_b

    # Org A repeats same key -> duplicate within Org A
    req_a2 = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id=org_a),
        payload={
            "event_type": "document.created",
            "source": "client_a",
            "idempotency_key": shared_key,
            "payload": {"doc": "A_retry"},
        },
    )
    resp_a2 = await engine.handle_record_event(req_a2)
    assert resp_a2.status == ResultStatus.SUCCESS
    assert resp_a2.payload["duplicate"] is True
    assert resp_a2.payload["observation_id"] == obs_id_a


@pytest.mark.asyncio
async def test_memory_engine_tenant_idempotency_isolation():
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    shared_key = "eng-mem-idemp-001"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"

    req_a1 = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(case_id="case_a", organization_id=org_a),
        payload={
            "payload": {"fact": "Org A legal conclusion"},
            "idempotency_key": shared_key,
            "record_type": "legal_fact",
        },
    )
    resp_a1 = await engine.handle_store_record(req_a1)
    assert resp_a1.status == ResultStatus.SUCCESS
    assert resp_a1.payload["duplicate"] is False
    rec_id_a = resp_a1.payload["record_id"]

    req_b1 = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(case_id="case_b", organization_id=org_b),
        payload={
            "payload": {"fact": "Org B legal conclusion"},
            "idempotency_key": shared_key,
            "record_type": "legal_fact",
        },
    )
    resp_b1 = await engine.handle_store_record(req_b1)
    assert resp_b1.status == ResultStatus.SUCCESS
    assert resp_b1.payload["duplicate"] is False
    rec_id_b = resp_b1.payload["record_id"]
    assert rec_id_a != rec_id_b

    # Org A retry returns existing record
    resp_a2 = await engine.handle_store_record(req_a1)
    assert resp_a2.status == ResultStatus.SUCCESS
    assert resp_a2.payload["duplicate"] is True
    assert resp_a2.payload["record_id"] == rec_id_a


@pytest.mark.asyncio
async def test_sqlalchemy_observation_store_tenant_idempotency(db_session: Session):
    store = SqlAlchemyObservationStore(db_session_factory=lambda: db_session)
    shared_key = f"db-obs-{uuid.uuid4().hex[:10]}"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"

    rec_a = {
        "id": str(uuid.uuid4()),
        "organization_id": org_a,
        "event_type": "contract.signed",
        "source": "test_suite",
        "idempotency_key": shared_key,
        "payload": {"org": "A", "val": 100},
    }
    rec_b = {
        "id": str(uuid.uuid4()),
        "organization_id": org_b,
        "event_type": "contract.signed",
        "source": "test_suite",
        "idempotency_key": shared_key,
        "payload": {"org": "B", "val": 200},
    }

    # Both must succeed without collision in PostgreSQL
    saved_a = await store.save(rec_a)
    saved_b = await store.save(rec_b)

    assert saved_a == rec_a["id"]
    assert saved_b == rec_b["id"]

    # Scoped lookup
    found_a = await store.find_by_idempotency_key(shared_key, organization_id=org_a)
    assert found_a is not None
    assert found_a["id"] == rec_a["id"]
    assert found_a["payload"]["org"] == "A"

    found_b = await store.find_by_idempotency_key(shared_key, organization_id=org_b)
    assert found_b is not None
    assert found_b["id"] == rec_b["id"]
    assert found_b["payload"]["org"] == "B"

    # Cross-tenant lookup returns None
    found_foreign = await store.find_by_idempotency_key(shared_key, organization_id=f"org_{uuid.uuid4().hex[:8]}")
    assert found_foreign is None

    # Intra-tenant duplicate must be rejected by PostgreSQL composite unique index
    rec_a_dup = {
        "id": str(uuid.uuid4()),
        "organization_id": org_a,
        "event_type": "contract.signed",
        "source": "test_suite",
        "idempotency_key": shared_key,
        "payload": {"org": "A_duplicate"},
    }
    with pytest.raises(IntegrityError):
        await store.save(rec_a_dup)
        db_session.flush()
    db_session.rollback()


@pytest.mark.asyncio
async def test_sqlalchemy_memory_store_tenant_idempotency(db_session: Session):
    store = SqlAlchemyMemoryStore(db_session_factory=lambda: db_session)
    shared_key = f"db-mem-{uuid.uuid4().hex[:10]}"
    org_a = f"org_{uuid.uuid4().hex[:8]}"
    org_b = f"org_{uuid.uuid4().hex[:8]}"

    uid_a = str(uuid.uuid4())
    uid_b = str(uuid.uuid4())
    rec_a = {
        "id": uid_a,
        "record_id": uid_a,
        "organization_id": org_a,
        "case_id": "case_001",
        "fact": "Tenant A fact",
        "idempotency_key": shared_key,
        "confidence": 0.9,
        "status": "candidate",
        "payload": {"fact": "Tenant A fact"},
    }
    rec_b = {
        "id": uid_b,
        "record_id": uid_b,
        "organization_id": org_b,
        "case_id": "case_002",
        "fact": "Tenant B fact",
        "idempotency_key": shared_key,
        "confidence": 0.8,
        "status": "candidate",
        "payload": {"fact": "Tenant B fact"},
    }

    # Both must succeed without collision in PostgreSQL
    saved_a = await store.save_record(rec_a)
    saved_b = await store.save_record(rec_b)

    assert saved_a == uid_a
    assert saved_b == uid_b

    # Scoped lookup
    found_a = await store.find_by_idempotency_key(shared_key, organization_id=org_a)
    assert found_a is not None
    assert found_a["id"] == rec_a["id"]

    found_b = await store.find_by_idempotency_key(shared_key, organization_id=org_b)
    assert found_b is not None
    assert found_b["id"] == rec_b["id"]

    # Cross-tenant lookup returns None
    found_foreign = await store.find_by_idempotency_key(shared_key, organization_id=f"org_{uuid.uuid4().hex[:8]}")
    assert found_foreign is None

    # Intra-tenant duplicate must be rejected by PostgreSQL composite unique index
    rec_a_dup = {
        "id": str(uuid.uuid4()),
        "record_id": str(uuid.uuid4()),
        "organization_id": org_a,
        "case_id": "case_001",
        "fact": "Tenant A duplicate fact",
        "idempotency_key": shared_key,
        "confidence": 0.9,
        "status": "candidate",
        "payload": {"fact": "Tenant A duplicate fact"},
    }
    with pytest.raises(IntegrityError):
        await store.save_record(rec_a_dup)
        db_session.flush()
    db_session.rollback()


@pytest.mark.asyncio
async def test_stores_reject_missing_or_blank_organization_id(db_session: Session):
    in_mem_obs = InMemoryObservationStore()
    in_mem_mem = InMemoryMemoryStore()
    sql_obs = SqlAlchemyObservationStore(db_session_factory=lambda: db_session)
    sql_mem = SqlAlchemyMemoryStore(db_session_factory=lambda: db_session)

    # 1. find_by_idempotency_key with invalid org
    for invalid_org in [None, "", "   "]:
        with pytest.raises(ValueError, match="organization_id must be a non-empty string"):
            await in_mem_obs.find_by_idempotency_key("k1", organization_id=invalid_org)  # type: ignore

        with pytest.raises(ValueError, match="organization_id must be a non-empty string"):
            await in_mem_mem.find_by_idempotency_key("k1", organization_id=invalid_org)  # type: ignore

        with pytest.raises(ValueError, match="organization_id must be a non-empty string"):
            await sql_obs.find_by_idempotency_key("k1", organization_id=invalid_org)  # type: ignore

        with pytest.raises(ValueError, match="organization_id must be a non-empty string"):
            await sql_mem.find_by_idempotency_key("k1", organization_id=invalid_org)  # type: ignore

    # 2. save / save_record with invalid org
    for invalid_org in [None, "", "   "]:
        with pytest.raises(ValueError, match="organization_id.*must be a non-empty string"):
            await in_mem_obs.save({"id": str(uuid.uuid4()), "organization_id": invalid_org})

        with pytest.raises(ValueError, match="organization_id.*must be a non-empty string"):
            await in_mem_mem.save_record({"id": str(uuid.uuid4()), "organization_id": invalid_org})

        with pytest.raises(ValueError, match="organization_id.*must be a non-empty string"):
            await sql_obs.save({"id": str(uuid.uuid4()), "organization_id": invalid_org})

        with pytest.raises(ValueError, match="organization_id.*must be a non-empty string"):
            await sql_mem.save_record({"id": str(uuid.uuid4()), "organization_id": invalid_org})


@pytest.mark.asyncio
async def test_observation_engine_adversarial_context_validation():
    store = InMemoryObservationStore()
    engine = ObservationEngine(store=store)

    # 1. Missing context_ref
    req_no_ctx = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        payload={"event_type": "doc.upload", "idempotency_key": "k-missing-ctx"},
    )
    resp = await engine.handle_record_event(req_no_ctx)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 2. String context_ref (unverified string)
    req_str_ctx = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref="ctx-unverified-string-id",
        payload={"event_type": "doc.upload", "idempotency_key": "k-str-ctx"},
    )
    resp = await engine.handle_record_event(req_str_ctx)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 3. ContextRef with missing organization_id
    req_empty_org = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id=""),
        payload={"event_type": "doc.upload", "idempotency_key": "k-empty-org"},
    )
    resp = await engine.handle_record_event(req_empty_org)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 4. Payload tenant spoofing (payload organization_id != context organization_id)
    req_spoof_org = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id="org-legit"),
        payload={
            "event_type": "doc.upload",
            "organization_id": "org-attacker-target",
            "idempotency_key": "k-spoof-org",
        },
    )
    resp = await engine.handle_record_event(req_spoof_org)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value

    # 5. Payload case mismatch
    req_spoof_case = MeshRequest(
        sender_engine="client",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ContextRef(organization_id="org-legit", case_id="case-100"),
        payload={
            "event_type": "doc.upload",
            "case_id": "case-999-victim",
            "idempotency_key": "k-spoof-case",
        },
    )
    resp = await engine.handle_record_event(req_spoof_case)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_memory_engine_adversarial_context_validation():
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    # 1. Missing context_ref
    req_no_ctx = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        payload={"payload": {"fact": "fact 1"}, "idempotency_key": "mem-no-ctx"},
    )
    resp = await engine.handle_store_record(req_no_ctx)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 2. String context_ref
    req_str_ctx = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref="ctx-string-ref",
        payload={"payload": {"fact": "fact 1"}, "idempotency_key": "mem-str-ctx"},
    )
    resp = await engine.handle_store_record(req_str_ctx)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 3. ContextRef with missing organization_id
    req_empty_org = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(case_id="case-1", organization_id=""),
        payload={"payload": {"fact": "fact 1"}, "idempotency_key": "mem-empty-org"},
    )
    resp = await engine.handle_store_record(req_empty_org)
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp.errors[0].code == EngineErrorCode.CONTEXT_MISSING.value

    # 4. Payload tenant spoofing
    req_spoof_org = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(case_id="case-1", organization_id="org-actual"),
        payload={
            "payload": {"fact": "fact 1"},
            "organization_id": "org-victim",
            "idempotency_key": "mem-spoof-org",
        },
    )
    resp = await engine.handle_store_record(req_spoof_org)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value

    # 5. Payload case mismatch
    req_spoof_case = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ContextRef(case_id="case-actual", organization_id="org-actual"),
        payload={
            "payload": {"fact": "fact 1"},
            "case_id": "case-foreign",
            "idempotency_key": "mem-spoof-case",
        },
    )
    resp = await engine.handle_store_record(req_spoof_case)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value


@pytest.mark.asyncio
async def test_postgresql_not_null_organization_id_enforcement(db_session: Session):
    """Verify that PostgreSQL rejects NULL organization_id at the database level."""
    # 1. Observation table NOT NULL constraint
    obs_invalid = Observation(
        id=uuid.uuid4(),
        event_id=f"evt-{uuid.uuid4().hex[:8]}",
        event_type="test.null_org",
        source="unit_test",
        organization_id=None,  # type: ignore
    )
    db_session.add(obs_invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()

    # 2. MemoryRecord table NOT NULL constraint
    mem_invalid = MemoryRecord(
        id=uuid.uuid4(),
        record_type="fact_candidate",
        organization_id=None,  # type: ignore
    )
    db_session.add(mem_invalid)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


@pytest.mark.asyncio
async def test_observation_engine_record_observation_tenant_validation():
    store = InMemoryObservationStore()
    engine = ObservationEngine(store=store)

    # 1. Missing or blank context organization
    res_no_ctx = await engine.record_observation(
        {"event_type": "doc.upload"},
        context=BrainContext(case_id="case-1", organization_id=""),
    )
    assert res_no_ctx.error is not None
    assert res_no_ctx.error["code"] == "INVALID_CONTEXT"

    # 2. Payload organization mismatch
    res_spoof = await engine.record_observation(
        {"event_type": "doc.upload", "organization_id": "org-foreign"},
        context=BrainContext(case_id="case-1", organization_id="org-legit"),
    )
    assert res_spoof.error is not None
    assert res_spoof.error["code"] == EngineErrorCode.AUTHORIZATION_DENIED.value

    # 3. Legitimate write and duplicate detection
    ctx = BrainContext(case_id="case-1", organization_id="org-legit")
    res1 = await engine.record_observation(
        {"event_type": "doc.upload", "idempotency_key": "obs-idem-1"},
        context=ctx,
    )
    assert res1.error is None
    assert res1.data["duplicate"] is False

    res2 = await engine.record_observation(
        {"event_type": "doc.upload", "idempotency_key": "obs-idem-1"},
        context=ctx,
    )
    assert res2.error is None
    assert res2.data["duplicate"] is True


@pytest.mark.asyncio
async def test_memory_engine_store_candidate_tenant_validation():
    store = InMemoryMemoryStore()
    engine = BasicMemoryEngine(store=store)

    # 1. Missing or blank context organization
    res_no_ctx = await engine.store_candidate(
        {"fact": "legal fact"},
        context=BrainContext(case_id="case-1", organization_id=""),
    )
    assert res_no_ctx.error is not None
    assert res_no_ctx.error["code"] == "INVALID_CONTEXT"

    # 2. Payload organization mismatch
    res_spoof = await engine.store_candidate(
        {"fact": "legal fact", "organization_id": "org-attacker"},
        context=BrainContext(case_id="case-1", organization_id="org-victim"),
    )
    assert res_spoof.error is not None
    assert res_spoof.error["code"] == EngineErrorCode.AUTHORIZATION_DENIED.value

    # 3. Legitimate store and duplicate detection
    ctx = BrainContext(case_id="case-1", organization_id="org-victim")
    res1 = await engine.store_candidate(
        {"fact": "legal fact", "idempotency_key": "mem-idem-1"},
        context=ctx,
    )
    assert res1.error is None
    assert res1.data.get("duplicate") is not True

    res2 = await engine.store_candidate(
        {"fact": "legal fact", "idempotency_key": "mem-idem-1"},
        context=ctx,
    )
    assert res2.error is None
    assert res2.data["duplicate"] is True
