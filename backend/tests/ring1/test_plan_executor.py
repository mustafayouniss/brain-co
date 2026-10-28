"""Tests for PlanStepExecutor and real plan step execution."""

import pytest

from app.ring1.contracts.capabilities import (
    CONTEXT_RESOLVE,
    MEMORY_STORE_RECORD,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import (
    Plan,
    PlanStatus,
    PlanStep,
    ReplanReasonCode,
    StepStatus,
)
from app.ring1.execution.executor import PlanStepExecutor


@pytest.fixture
def ctx_ref() -> ContextRef:
    return ContextRef(
        organization_id="org-acme",
        case_id="case-100",
        domain_id="corporate",
        status=ResolutionStatus.EXPLICIT,
    )


@pytest.mark.asyncio
async def test_executor_successful_step_execution(ring1_mesh, ctx_ref):
    """A valid plan step executes through MeshRouter and becomes COMPLETED with actual_result."""
    router = ring1_mesh["router"]
    registry = ring1_mesh["registry"]
    executor = PlanStepExecutor(router=router, registry=registry)

    step = PlanStep(
        order=1,
        capability=PERCEPTION_STRUCTURE_INPUT,
        description="Structure raw corporate input.",
    )
    plan = Plan(
        task_id="task-001",
        goal="Parse financial summary",
        steps=[step],
        context_ref=ctx_ref.ref,
    )

    resp, status = await executor.execute_step(plan, step, context_ref=ctx_ref)
    assert status == StepStatus.COMPLETED
    assert step.status == StepStatus.COMPLETED
    assert resp.status == ResultStatus.SUCCESS
    assert step.actual_result is not None
    assert "structured_content" in step.actual_result


@pytest.mark.asyncio
async def test_executor_failed_capability_produces_failed_step(ring1_mesh, ctx_ref):
    """When a capability fails at runtime, the step becomes FAILED with real error evidence."""
    router = ring1_mesh["router"]
    registry = ring1_mesh["registry"]
    executor = PlanStepExecutor(router=router, registry=registry)

    # Retrieval without case_id in ContextRef or payload will genuinely fail with CONTEXT_MISSING
    invalid_ctx = ContextRef(
        organization_id="org-acme",
        case_id=None,  # Missing mandatory case_id for retrieval
        status=ResolutionStatus.INSUFFICIENT_DATA,
    )
    step = PlanStep(
        order=1,
        capability=RETRIEVAL_QUERY,
        description="Query case documents without case_id",
    )
    plan = Plan(
        task_id="task-002",
        goal="Query without case context",
        steps=[step],
    )

    resp, status = await executor.execute_step(plan, step, context_ref=invalid_ctx)
    assert status == StepStatus.FAILED
    assert step.status == StepStatus.FAILED
    assert resp.status == ResultStatus.NEEDS_CLARIFICATION
    assert step.actual_result["status"] == ResultStatus.NEEDS_CLARIFICATION.value


@pytest.mark.asyncio
async def test_executor_unregistered_capability_rejected(ring1_mesh, ctx_ref):
    """A step with an unknown capability is rejected before dispatch."""
    router = ring1_mesh["router"]
    registry = ring1_mesh["registry"]
    executor = PlanStepExecutor(router=router, registry=registry)

    step = PlanStep(
        order=1,
        capability="unregistered.magic_wand",
        description="Non-existent capability",
    )
    plan = Plan(task_id="task-003", goal="Test invalid cap", steps=[step])

    resp, status = await executor.execute_step(plan, step, context_ref=ctx_ref)
    assert status == StepStatus.FAILED
    assert step.status == StepStatus.FAILED
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.CAPABILITY_NOT_FOUND.value


@pytest.mark.asyncio
async def test_executor_full_plan_lifecycle_with_retention(ring1_mesh, ctx_ref):
    """Full plan executes sequentially; completed steps are preserved during replanning."""
    router = ring1_mesh["router"]
    registry = ring1_mesh["registry"]
    planning = ring1_mesh["planning"]

    # 1. Create a plan with 2 steps
    step1 = PlanStep(order=1, capability=PERCEPTION_STRUCTURE_INPUT, description="Step 1")
    step2 = PlanStep(order=2, capability=CONTEXT_RESOLVE, description="Step 2")
    plan = Plan(
        task_id="task-004",
        goal="Two-step plan",
        steps=[step1, step2],
        context_ref=ctx_ref.ref,
    )
    planning._plans[plan.plan_id] = plan

    # 2. Execute with fault injection on step 2 to simulate boundary failure
    def boundary_fault_injector(s: PlanStep, req: MeshRequest):
        if s.order == 2:
            # Strip context_hint to cause ContextEngine to return NEEDS_CLARIFICATION
            return MeshRequest(
                task_id=req.task_id,
                plan_version=req.plan_version,
                sender_engine=req.sender_engine,
                recipient_capability=req.recipient_capability,
                payload={},  # Missing context_hint
            )
        return None

    executor = PlanStepExecutor(router=router, registry=registry, fault_injector=boundary_fault_injector)

    # Execute plan steps
    events = []
    async for event in executor.execute_plan(plan, context_ref=ctx_ref):
        events.append(event)

    # Step 1 should be completed
    assert step1.status == StepStatus.COMPLETED
    assert step1.actual_result is not None

    # Step 2 should be genuinely failed
    assert step2.status == StepStatus.FAILED
    assert plan.can_replan() is True

    # 3. Trigger evidence-based replan
    replan_req = MeshRequest(
        sender_engine="plan_executor",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        context_ref=ctx_ref,
        payload={
            "plan_id": plan.plan_id,
            "failed_step_id": step2.step_id,
            "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
            "evidence": {"missing_attributes": ["case_id"]},
            "actual_result": step2.actual_result,
        },
    )
    replan_resp = await router.dispatch(replan_req)
    assert replan_resp.status == ResultStatus.SUCCESS
    assert replan_resp.payload["new_version"] == 2
    assert step1.step_id in replan_resp.payload["steps_retained"]

    # 4. Execute revised Plan v2 without fault injector
    revised_plan = planning._plans[plan.plan_id]
    normal_executor = PlanStepExecutor(router=router, registry=registry)
    v2_events = []
    async for event in normal_executor.execute_plan(revised_plan, context_ref=ctx_ref):
        v2_events.append(event)

    # Verified: Step 1 remained completed (was retained), newly added recovery step completed
    assert step1.status == StepStatus.COMPLETED
    assert any(e["event_type"] == "step_retained" for e in v2_events)
    assert revised_plan.status == PlanStatus.COMPLETED


@pytest.mark.asyncio
async def test_replan_limit_exhaustion_terminates_plan(ring1_mesh, ctx_ref):
    """Exhausting max_replans cleanly fails and terminates the plan."""
    router = ring1_mesh["router"]
    planning = ring1_mesh["planning"]

    step = PlanStep(order=1, capability=RETRIEVAL_QUERY, status=StepStatus.FAILED)
    plan = Plan(
        task_id="task-005",
        goal="Exhaust limit",
        steps=[step],
        max_replans=1,
        replan_count=1,  # Already at limit
    )
    planning._plans[plan.plan_id] = plan

    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        context_ref=ctx_ref,
        payload={
            "plan_id": plan.plan_id,
            "failed_step_id": step.step_id,
            "reason_code": ReplanReasonCode.CAPABILITY_FAILED.value,
        },
    )
    resp = await router.dispatch(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.REPLAN_LIMIT_EXCEEDED.value
    assert plan.status == PlanStatus.FAILED
