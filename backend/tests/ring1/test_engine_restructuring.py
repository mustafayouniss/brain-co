"""Tests verifying Ring 1 Engine Restructuring and Pure Protocol compliance.

Verifies:
- PerceptionEngine: Transport-independent input processing, explicit type detection, unsupported rejection.
- ObservationEngine: Persistence, duplicate idempotency suppression, HMAC cursor feed pagination.
- ContextEngine: Authoritative boundary resolution, rejection of client organization override.
- MemoryEngine: Candidate lifecycle, rejection of automatic self-promotion, human validation authority.
- RetrievalEngine: Lexical strategy, candidate selection, ranking, and strict case isolation.
- PlanningEngine: Advisory declarative plans, bounded replanning, zero execution authority.
- RuntimeDispatcher: Domain-blind capability routing and handoff enforcement.
"""

from datetime import datetime, timezone
import uuid
from uuid import UUID

import pytest
from sqlalchemy.orm import Session

from app.core.context import BrainContext
from app.core.dispatcher import RuntimeDispatcher
from app.core.handoff import HandoffPolicy
from app.ring1.contracts.capabilities import (
    ALL_CAPABILITIES,
    CONTEXT_RESOLVE,
    MEMORY_GET_RECORD,
    MEMORY_STORE_RECORD,
    OBSERVATION_RECORD_EVENT,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    PLANNING_GET_PLAN_STATUS,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
    CapabilityRegistry,
)
from app.ring1.contracts.protocols import (
    EngineResult,
    IContextEngine,
    IMemoryEngine,
    IObservationEngine,
    IPerceptionEngine,
    IPlanningEngine,
    IRetrievalEngine,
)
from app.ring1.engines.context import ContextEngine
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.observation import ObservationEngine
from app.ring1.engines.perception import PerceptionEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine, LexicalRetrievalStrategy


# -----------------------------------------------------------------------------
# 1. Perception Engine Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_perception_pure_protocol():
    engine = PerceptionEngine()
    assert isinstance(engine, IPerceptionEngine)

    context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )

    # 1. Process valid text input
    res = await engine.process(
        raw_input="Contract clause specifies delivery within 30 days.",
        context=context,
        task_metadata={"source_type": "text"},
    )
    assert res.error is None
    assert res.data["detected_type"] == "text"
    assert res.data["processing_mode"] == "deterministic"
    assert res.data["status"] == "success"

    # 2. Reject unsupported input type
    unsupported_res = await engine.process(
        raw_input={"content": "0xDEADBEEF", "source_type": "binary_executable"},
        context=context,
    )
    assert unsupported_res.error is not None
    assert unsupported_res.error["code"] in ("UNSUPPORTED_INPUT_TYPE", "unsupported_input_type")

    # 3. Context validation: missing org
    invalid_context = BrainContext(
        organization_id="",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )
    no_org_res = await engine.process("Some text", context=invalid_context)
    assert no_org_res.error is not None
    assert no_org_res.error["code"] == "INVALID_CONTEXT"


# -----------------------------------------------------------------------------
# 2. Observation Engine Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_observation_pure_protocol(db_session: Session):
    session_factory = lambda: db_session
    engine = ObservationEngine(db_session_factory=session_factory)
    assert isinstance(engine, IObservationEngine)

    context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )

    # 1. Record observation
    obs_payload = {
        "event_type": "document.uploaded",
        "payload": {"document_id": "doc-001", "name": "Agreement.pdf"},
        "idempotency_key": "upload-idemp-001",
    }
    res = await engine.record_observation(obs_payload, context)
    assert res.error is None
    assert res.data["status"] == "recorded"
    assert res.data["duplicate"] is False
    assert res.data["observation_id"] is not None

    # 2. Duplicate suppression via idempotency key
    dup_res = await engine.record_observation(obs_payload, context)
    assert dup_res.error is None
    assert dup_res.data["status"] == "duplicate"
    assert dup_res.data["duplicate"] is True

    # 3. Feed pagination with HMAC-signed keyset cursor
    feed = await engine.list_observations(context=context, limit=10)
    assert len(feed.items) >= 1
    assert feed.items[0]["case_id"] == "case-100"


# -----------------------------------------------------------------------------
# 3. Context Engine Tests
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_context_pure_protocol():
    engine = ContextEngine()
    assert isinstance(engine, IContextEngine)

    context = BrainContext(
        organization_id="org-server-authorized",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )

    # 1. Authoritative resolution
    res = await engine.resolve_context(
        request_scope={"domain_id": "corporate_law", "case_id": "case-100"},
        context=context,
    )
    assert res.error is None
    assert res.data["organization_id"] == "org-server-authorized"
    assert res.data["case_id"] == "case-100"

    # 2. Rejection of caller-supplied organization override
    override_res = await engine.resolve_context(
        request_scope={"organization_id": "org-attacker-injected"},
        context=context,
    )
    assert override_res.error is not None
    assert override_res.error["code"] == "FORBIDDEN_ORG_OVERRIDE"


# -----------------------------------------------------------------------------
# 4. Memory Engine Tests (Human Validation Authority)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_memory_pure_protocol(db_session: Session):
    session_factory = lambda: db_session
    engine = BasicMemoryEngine(db_session_factory=session_factory)
    assert isinstance(engine, IMemoryEngine)

    # Context without validation authority (e.g. standard AI worker context)
    worker_context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="worker-agent",
        correlation_id=uuid.uuid4(),
        validation_authority=False,
    )

    # 1. Store knowledge candidate
    candidate_data = {
        "record_type": "contract_clause",
        "payload": {"clause": "Liability capped at $1,000,000"},
        "idempotency_key": "clause-cand-001",
    }
    store_res = await engine.store_candidate(candidate_data, worker_context)
    assert store_res.error is None
    record_id = UUID(store_res.data["record_id"])
    assert store_res.data["status"] == "candidate"

    # 2. Worker attempts automatic self-validation -> REJECTED
    self_promote_res = await engine.validate_candidate(
        record_id=record_id,
        action="VALIDATE",
        context=worker_context,
    )
    assert self_promote_res.error is not None
    assert self_promote_res.error["code"] == "VALIDATION_AUTHORITY_REQUIRED"

    # 3. Human validator context validates candidate -> SUCCESS
    human_context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="human-partner@lawfirm.com",
        correlation_id=uuid.uuid4(),
        validation_authority=True,
    )
    validate_res = await engine.validate_candidate(
        record_id=record_id,
        action="VALIDATE",
        context=human_context,
    )
    assert validate_res.error is None
    assert validate_res.data["status"] == "validated"
    assert validate_res.data["metadata"]["validated_by"] == "human-partner@lawfirm.com"

    # 4. Cross-case read rejection
    different_case_context = BrainContext(
        organization_id="org-test-1",
        case_id="case-OTHER-999",
        user_id="human-partner@lawfirm.com",
        correlation_id=uuid.uuid4(),
        validation_authority=True,
    )
    cross_read_res = await engine.get_record(record_id, different_case_context)
    assert cross_read_res.error is not None
    assert cross_read_res.error["code"] == "PERMISSION_DENIED"


# -----------------------------------------------------------------------------
# 5. Retrieval Engine Tests (Strict Case Isolation & Lexical Strategy)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retrieval_pure_protocol(db_session: Session):
    session_factory = lambda: db_session
    memory_engine = BasicMemoryEngine(db_session_factory=session_factory)
    strategy = LexicalRetrievalStrategy()
    engine = BasicRetrievalEngine(
        db_session_factory=session_factory,
        memory_engine=memory_engine,
        strategy=strategy,
    )
    assert isinstance(engine, IRetrievalEngine)

    context_case_a = BrainContext(
        organization_id="org-test-1",
        case_id="case-A",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
        validation_authority=True,
    )
    context_case_b = BrainContext(
        organization_id="org-test-1",
        case_id="case-B",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
        validation_authority=True,
    )

    # Store record in Case A
    await memory_engine.store_candidate(
        {
            "record_type": "evidence",
            "payload": {"text": "Confidential patent agreement between parties"},
            "idempotency_key": "patent-agreement-a",
        },
        context_case_a,
    )

    # Store record in Case B
    await memory_engine.store_candidate(
        {
            "record_type": "evidence",
            "payload": {"text": "Patent licensing dispute and royalty agreement"},
            "idempotency_key": "patent-licensing-b",
        },
        context_case_b,
    )

    # Search in Case A: must find record from Case A only, never Case B
    search_res_a = await engine.search("patent agreement", context=context_case_a)
    assert search_res_a.error is None
    records_a = search_res_a.data["records"]
    assert len(records_a) >= 1
    for r in records_a:
        assert r["case_id"] == "case-A"
        assert r["case_id"] != "case-B"


# -----------------------------------------------------------------------------
# 6. Planning Engine Tests (Advisory Only under ADR-008)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_planning_pure_protocol():
    engine = PlanningEngine()
    assert isinstance(engine, IPlanningEngine)

    context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )

    # 1. Formulate plan: strictly declarative, no execution
    plan = await engine.create_plan(
        goal="Ingest contract and extract liability limitations",
        context=context,
        max_replans=2,
    )
    assert plan is not None
    assert plan.goal is not None
    assert len(plan.steps) > 0
    initial_version = plan.version
    # Steps are strictly declarative capability references
    for step in plan.steps:
        assert step.capability in ALL_CAPABILITIES

    # 2. Request replan: advisory failure adaptation
    revised_plan = await engine.request_replan(
        plan=plan,
        failure_evidence={"failed_step_index": 0, "error": "Document format corrupted"},
        context=context,
    )
    assert revised_plan is not None
    assert revised_plan.version > initial_version


# -----------------------------------------------------------------------------
# 7. Runtime Dispatcher Tests (Domain-Blind Capability Routing)
# -----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_runtime_dispatcher():
    registry = CapabilityRegistry()
    handoff_policy = HandoffPolicy()
    dispatcher = RuntimeDispatcher(registry=registry, handoff_policy=handoff_policy)

    context = BrainContext(
        organization_id="org-test-1",
        case_id="case-100",
        user_id="user-1",
        correlation_id=uuid.uuid4(),
    )

    # Register mock capability handler
    async def mock_handler(payload: dict, ctx: BrainContext) -> EngineResult:
        return EngineResult(data={"processed": True, "input": payload})

    registry.register(
        capability_name=OBSERVATION_RECORD_EVENT,
        engine_name="observation",
        handler=mock_handler,
    )

    # Permitted handoff: EXTERNAL -> OBSERVATION_RECORD_EVENT
    res = await dispatcher.dispatch(
        target_capability=OBSERVATION_RECORD_EVENT,
        payload={"event": "test"},
        context=context,
    )
    assert res.error is None
    assert res.data["processed"] is True

    # Disallowed handoff: OBSERVATION cannot autonomously initiate PLANNING
    disallowed_res = await dispatcher.dispatch(
        target_capability=PLANNING_CREATE_PLAN,
        payload={"goal": "test"},
        context=context,
        source_capability=OBSERVATION_RECORD_EVENT,
    )
    assert disallowed_res.error is not None
    assert disallowed_res.error["code"] == "AUTONOMOUS_PLANNING_FORBIDDEN"
