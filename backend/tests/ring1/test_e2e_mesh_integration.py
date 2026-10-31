"""End-to-End Integration Test for all Six Ring 1 Engines.

Exercises:
1. Perception Engine (deterministic JSON input structuring)
2. Observation Engine (event recording, deduplication via idempotency)
3. Context Engine (scope boundary resolution, ambiguity detection)
4. Basic Memory Engine (context-isolated persistence in PostgreSQL)
5. Basic Retrieval Engine (case-scoped query and strict cross-case data isolation)
6. Planning Engine (plan creation, step execution, forced failure, and bounded replanning)

All six engines communicate strictly through MeshRouter.dispatch() and peer delegation.
Uses real PostgreSQL test database via db_session fixture.
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from sqlalchemy.orm import Session

from ai.core.services.llm_service import LLMService
from ai.providers.fake_provider import FakeLLMProvider
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
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import PlanStatus, ReplanReasonCode, StepStatus
from app.ring1.engines.context import ContextEngine
from ai.core.interfaces.provider import ILLMProvider
from app.ring1.engines.memory import BasicMemoryEngine
from app.ring1.engines.observation import ObservationEngine
from app.ring1.engines.perception import PerceptionEngine
from app.ring1.engines.planning import PlanningEngine
from app.ring1.engines.retrieval import BasicRetrievalEngine
from app.ring1.mesh.router import MeshRouter


class StructuredTraceCollector:
    """Structured in-memory trace collector for end-to-end integration observability."""

    def __init__(self):
        self.entries: list[dict[str, Any]] = []

    def log(
        self,
        event: str,
        *,
        engine: str,
        capability: str,
        status: str,
        task_id: str | None = None,
        trace_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.entries.append({
            "event": event,
            "engine": engine,
            "capability": capability,
            "status": status,
            "task_id": task_id,
            "trace_id": trace_id,
            "details": details or {},
        })


@pytest.fixture
def mesh_system(db_session: Session):
    """Setup real MeshRouter and all six engines wired to the test PostgreSQL database."""
    fake_provider = FakeLLMProvider()
    llm_service = LLMService(provider=fake_provider)
    registry = CapabilityRegistry()
    router = MeshRouter(registry=registry, default_timeout_seconds=10.0)

    # Session factory returning the transactional test session
    session_factory = lambda: db_session

    perception = PerceptionEngine(llm_service=llm_service, mesh_router=router)
    observation = ObservationEngine(
        db_session_factory=session_factory,
        llm_service=llm_service,
        mesh_router=router,
    )
    context = ContextEngine(llm_service=llm_service, mesh_router=router)
    memory = BasicMemoryEngine(
        db_session_factory=session_factory,
        llm_service=llm_service,
        mesh_router=router,
    )
    retrieval = BasicRetrievalEngine(
        db_session_factory=session_factory,
        memory_engine=memory,
        llm_service=llm_service,
        mesh_router=router,
    )
    planning = PlanningEngine(llm_service=llm_service, mesh_router=router)

    # Register all 6 engines
    perception.register_capabilities(registry)
    observation.register_capabilities(registry)
    context.register_capabilities(registry)
    memory.register_capabilities(registry)
    retrieval.register_capabilities(registry)
    planning.register_capabilities(registry)

    tracer = StructuredTraceCollector()

    return {
        "router": router,
        "registry": registry,
        "tracer": tracer,
        "perception": perception,
        "observation": observation,
        "context": context,
        "memory": memory,
        "retrieval": retrieval,
        "planning": planning,
    }


@pytest.mark.asyncio
async def test_full_ring1_mesh_lifecycle_e2e(mesh_system):
    """Execute full realistic end-to-end scenario exercising all six engines."""
    router: MeshRouter = mesh_system["router"]
    tracer: StructuredTraceCollector = mesh_system["tracer"]
    planning_engine: PlanningEngine = mesh_system["planning"]

    org_id = "org-synthetic-corp"
    primary_case_id = "case-legal-888"
    adversary_case_id = "case-foreign-999"

    # =========================================================================
    # Phase 2.A: Perception Engine
    # =========================================================================
    raw_memo = json.dumps({
        "memo_title": "Synthetic NDA Breach Assessment",
        "case_id": primary_case_id,
        "suspect": "John Doe",
        "evidence_summary": "Defendant disclosed proprietary source code on 2026-09-15",
        "jurisdiction": "Civil Court Cairo",
    })

    req_perception = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": raw_memo, "input_type": "json"},
    )
    resp_perception = await router.dispatch(req_perception)

    tracer.log(
        "PerceptionProcessed",
        engine=resp_perception.sender_engine,
        capability=PERCEPTION_STRUCTURE_INPUT,
        status=resp_perception.status.value,
        task_id=req_perception.task_id,
        trace_id=req_perception.trace_id,
        details={"detected_type": resp_perception.payload.get("detected_type")},
    )

    assert resp_perception.status == ResultStatus.SUCCESS
    assert resp_perception.payload["detected_type"] == "json"
    parsed_memo = resp_perception.payload["parsed_content"]
    assert parsed_memo["memo_title"] == "Synthetic NDA Breach Assessment"
    assert resp_perception.payload["extracted_metadata"]["key_count"] == 5

    # =========================================================================
    # Phase 2.C: Context Engine
    # =========================================================================
    # 1. Valid resolution for Primary Case A
    req_context_a = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        payload={
            "context_hint": {
                "organization_id": org_id,
                "case_id": primary_case_id,
                "domain_id": "intellectual_property",
            }
        },
    )
    resp_context_a = await router.dispatch(req_context_a)

    tracer.log(
        "ContextResolved",
        engine=resp_context_a.sender_engine,
        capability=CONTEXT_RESOLVE,
        status=resp_context_a.status.value,
        task_id=req_context_a.task_id,
        trace_id=req_context_a.trace_id,
        details={"case_id": resp_context_a.payload.get("case_id")},
    )

    assert resp_context_a.status == ResultStatus.SUCCESS
    assert resp_context_a.payload["status"] == ResolutionStatus.EXPLICIT.value
    assert resp_context_a.payload["case_id"] == primary_case_id
    context_ref_a_str = resp_context_a.payload["context_ref"]

    ctx_ref_a = ContextRef(
        context_ref_id=context_ref_a_str,
        organization_id=org_id,
        case_id=primary_case_id,
        domain_id="intellectual_property",
        resolution_status=ResolutionStatus.EXPLICIT,
    )

    # 2. Negative test: Missing case_id fails with AMBIGUOUS / NEEDS_CLARIFICATION
    req_context_invalid = MeshRequest(
        sender_engine="client",
        recipient_capability=CONTEXT_RESOLVE,
        payload={"context_hint": {"organization_id": org_id}},  # missing case_id
    )
    resp_context_invalid = await router.dispatch(req_context_invalid)
    assert resp_context_invalid.status == ResultStatus.NEEDS_CLARIFICATION
    assert resp_context_invalid.payload["status"] == ResolutionStatus.AMBIGUOUS.value

    # =========================================================================
    # Phase 2.B: Observation Engine
    # =========================================================================
    idempotency_key = "evt-nda-memo-uploaded-888"
    req_observation = MeshRequest(
        sender_engine="perception",
        recipient_capability=OBSERVATION_RECORD_EVENT,
        context_ref=ctx_ref_a,
        payload={
            "event_type": "document.uploaded",
            "source": "legal_gateway",
            "idempotency_key": idempotency_key,
            "payload": parsed_memo,
        },
    )
    resp_obs1 = await router.dispatch(req_observation)

    tracer.log(
        "ObservationRecorded",
        engine=resp_obs1.sender_engine,
        capability=OBSERVATION_RECORD_EVENT,
        status=resp_obs1.status.value,
        task_id=req_observation.task_id,
        trace_id=req_observation.trace_id,
        details={"duplicate": resp_obs1.payload.get("duplicate")},
    )

    assert resp_obs1.status == ResultStatus.SUCCESS
    assert resp_obs1.payload["duplicate"] is False
    assert resp_obs1.payload["follow_up_required"] is True
    obs_id = resp_obs1.payload["observation_id"]

    # Deduplication test: Repeat exact same event
    resp_obs2 = await router.dispatch(req_observation)
    assert resp_obs2.status == ResultStatus.SUCCESS
    assert resp_obs2.payload["duplicate"] is True
    assert resp_obs2.payload["observation_id"] == obs_id

    # =========================================================================
    # Phase 2.D: Basic Memory Engine
    # =========================================================================
    req_store_fact = MeshRequest(
        sender_engine="observation",
        recipient_capability=MEMORY_STORE_RECORD,
        context_ref=ctx_ref_a,
        payload={
            "record_type": "covenant_breach_fact",
            "payload": {
                "claim": "Defendant disclosed proprietary source code on 2026-09-15",
                "severity": "critical",
                "suspect": "John Doe",
            },
            "source_observation_id": obs_id,
            "idempotency_key": "fact-nda-sourcecode-disclosure",
        },
    )
    resp_store = await router.dispatch(req_store_fact)

    tracer.log(
        "MemoryStored",
        engine=resp_store.sender_engine,
        capability=MEMORY_STORE_RECORD,
        status=resp_store.status.value,
        task_id=req_store_fact.task_id,
        trace_id=req_store_fact.trace_id,
        details={"record_id": resp_store.payload.get("record_id")},
    )

    assert resp_store.status == ResultStatus.SUCCESS
    assert resp_store.payload["duplicate"] is False
    record_id_a = resp_store.payload["record_id"]

    # =========================================================================
    # Phase 2.E: Basic Retrieval & Strict Case Isolation
    # =========================================================================
    # 1. Retrieval in authorized Case A -> must succeed and find the record
    req_retrieve_a = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_ref_a,
        payload={"query": "source code", "record_type": "covenant_breach_fact"},
    )
    resp_retrieve_a = await router.dispatch(req_retrieve_a)

    tracer.log(
        "RetrievalQueriedCaseA",
        engine=resp_retrieve_a.sender_engine,
        capability=RETRIEVAL_QUERY,
        status=resp_retrieve_a.status.value,
        task_id=req_retrieve_a.task_id,
        trace_id=req_retrieve_a.trace_id,
        details={"records_found": len(resp_retrieve_a.payload.get("records", []))},
    )

    assert resp_retrieve_a.status == ResultStatus.SUCCESS
    records_a = resp_retrieve_a.payload["records"]
    assert len(records_a) == 1
    assert records_a[0]["record_id"] == record_id_a
    assert records_a[0]["case_id"] == primary_case_id

    # 2. Retrieval from adversary Case B context -> zero records returned
    ctx_ref_b = ContextRef(
        organization_id=org_id,
        case_id=adversary_case_id,
        domain_id="intellectual_property",
        resolution_status=ResolutionStatus.EXPLICIT,
    )
    req_retrieve_b = MeshRequest(
        sender_engine="client",
        recipient_capability=RETRIEVAL_QUERY,
        context_ref=ctx_ref_b,
        payload={"query": "source code"},
    )
    resp_retrieve_b = await router.dispatch(req_retrieve_b)
    assert resp_retrieve_b.status == ResultStatus.SUCCESS
    assert len(resp_retrieve_b.payload["records"]) == 0

    # 3. Direct GET from Case B for Case A record -> rejected with AUTHORIZATION_DENIED
    req_hack_get = MeshRequest(
        sender_engine="client",
        recipient_capability=MEMORY_GET_RECORD,
        context_ref=ctx_ref_b,
        payload={"record_id": record_id_a},
    )
    resp_hack_get = await router.dispatch(req_hack_get)
    assert resp_hack_get.status == ResultStatus.FAILED
    assert resp_hack_get.errors[0].code == EngineErrorCode.AUTHORIZATION_DENIED.value

    # =========================================================================
    # Phase 2.F & Phase 3: Planning Engine & Forced Replan Lifecycle
    # =========================================================================
    # 1. Create initial plan
    req_create_plan = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        context_ref=ctx_ref_a,
        payload={
            "goal": "Audit covenant breach and index proprietary source code disclosure",
            "max_replans": 2,
        },
    )
    resp_create_plan = await router.dispatch(req_create_plan)

    assert resp_create_plan.status == ResultStatus.SUCCESS
    plan_id = resp_create_plan.payload["plan_id"]
    initial_version = resp_create_plan.payload["version"]
    assert initial_version == 1
    assert resp_create_plan.payload["status"] == PlanStatus.ACTIVE.value
    steps = resp_create_plan.payload["steps"]
    assert len(steps) >= 4

    # Verify all steps in allowlist
    for s in steps:
        assert s["capability"] in ALL_CAPABILITIES

    tracer.log(
        "PlanCreated",
        engine=resp_create_plan.sender_engine,
        capability=PLANNING_CREATE_PLAN,
        status=resp_create_plan.status.value,
        task_id=req_create_plan.task_id,
        trace_id=req_create_plan.trace_id,
        details={"plan_id": plan_id, "version": initial_version, "steps": len(steps)},
    )

    # 2. Execute Step 1 (perception) and preserve completion state
    step_1 = steps[0]
    active_plan = planning_engine._plans[plan_id]
    active_plan.steps[0].status = StepStatus.COMPLETED
    active_plan.steps[0].actual_result = {"parsed_keys": 5, "status": "success"}

    assert len(active_plan.get_completed_steps()) == 1

    # 3. Force controlled failure on Step 2 (context insufficiency)
    step_2 = steps[1]
    failed_step_id = step_2["step_id"]

    # 4. Trigger Replan via Planning Engine
    req_replan = MeshRequest(
        sender_engine="execution_runner",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        context_ref=ctx_ref_a,
        payload={
            "plan_id": plan_id,
            "failed_step_id": failed_step_id,
            "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
            "evidence": {
                "error": "Case boundaries required refinement",
                "missing_attributes": ["domain_id"],
            },
        },
    )
    resp_replan = await router.dispatch(req_replan)

    tracer.log(
        "PlanReplanned",
        engine=resp_replan.sender_engine,
        capability=PLANNING_REQUEST_REPLAN,
        status=resp_replan.status.value,
        task_id=req_replan.task_id,
        trace_id=req_replan.trace_id,
        details={
            "plan_id": plan_id,
            "old_version": initial_version,
            "new_version": resp_replan.payload.get("new_version"),
        },
    )

    assert resp_replan.status == ResultStatus.SUCCESS
    replan_data = resp_replan.payload
    assert replan_data["new_version"] == 2
    assert step_1["step_id"] in replan_data["steps_retained"]
    assert len(replan_data["steps_added"]) > 0

    # 5. Query plan status and verify preserved completion state
    req_plan_status = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_GET_PLAN_STATUS,
        payload={"plan_id": plan_id},
    )
    resp_status = await router.dispatch(req_plan_status)
    assert resp_status.status == ResultStatus.SUCCESS
    status_data = resp_status.payload
    assert status_data["version"] == 2
    assert status_data["replan_count"] == 1
    assert status_data["completed_steps"] == 1
    assert status_data["status"] == PlanStatus.ACTIVE.value

    # Verify that the structured trace collected records for all 6 engines
    engines_in_trace = {entry["engine"] for entry in tracer.entries}
    assert "perception" in engines_in_trace
    assert "observation" in engines_in_trace
    assert "context" in engines_in_trace
    assert "memory" in engines_in_trace
    assert "retrieval" in engines_in_trace
    assert "planning" in engines_in_trace
