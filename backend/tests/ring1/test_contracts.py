"""Tests for Ring 1 contracts: envelopes, capabilities, errors, plan models."""

import pytest
from pydantic import ValidationError

from app.ring1.contracts.capabilities import (
    ALL_CAPABILITIES,
    PERCEPTION_STRUCTURE_INPUT,
    CapabilityRegistry,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import (
    PROTOCOL_VERSION,
    DelegationConstraints,
    MeshError,
    MeshRequest,
    MeshResponse,
    ResultStatus,
)
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import Plan, PlanStatus, PlanStep, StepStatus


def test_mesh_request_defaults():
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": "test payload"},
    )
    assert req.protocol_version == PROTOCOL_VERSION
    assert req.message_id.startswith("msg-")
    assert req.task_id.startswith("task-")
    assert req.trace_id.startswith("trace-")
    assert req.constraints.max_delegations_remaining == 10


def test_mesh_request_validation():
    with pytest.raises(ValidationError):
        # Missing required fields
        MeshRequest(sender_engine="client")  # type: ignore


def test_mesh_response_factories():
    req = MeshRequest(
        sender_engine="test",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={},
    )

    success_resp = MeshResponse.success(
        request=req,
        sender_engine="perception",
        payload={"parsed": True},
        context_ref="ctx-123",
    )
    assert success_resp.status == ResultStatus.SUCCESS
    assert success_resp.payload == {"parsed": True}
    assert success_resp.correlation_id == req.message_id
    assert success_resp.task_id == req.task_id
    assert success_resp.context_ref == "ctx-123"

    fail_resp = MeshResponse.failure(
        request=req,
        sender_engine="perception",
        status=ResultStatus.FAILED,
        errors=[
            MeshError(
                code=EngineErrorCode.PARSING_FAILED.value,
                message="Cannot parse input",
                engine="perception",
            )
        ],
    )
    assert fail_resp.status == ResultStatus.FAILED
    assert len(fail_resp.errors) == 1
    assert fail_resp.errors[0].code == EngineErrorCode.PARSING_FAILED.value


def test_context_ref_model():
    ctx = ContextRef(
        organization_id="org-1",
        domain_id="legal",
        case_id="case-100",
        resolution_status=ResolutionStatus.EXPLICIT,
    )
    assert ctx.is_resolved is True
    assert ctx.case_id == "case-100"
    assert ctx.ref.startswith("ctx-")



def test_capability_registry():
    registry = CapabilityRegistry()
    assert len(registry.list_capabilities()) == 0

    async def dummy_handler(req):
        return MeshResponse.success(req, "test", {})

    registry.register(
        PERCEPTION_STRUCTURE_INPUT,
        "perception",
        dummy_handler,
        description="Test description",
    )
    assert registry.is_registered(PERCEPTION_STRUCTURE_INPUT)
    assert registry.get_handler(PERCEPTION_STRUCTURE_INPUT) == dummy_handler

    # Re-registering should raise ValueError
    with pytest.raises(ValueError, match="already registered"):
        registry.register(PERCEPTION_STRUCTURE_INPUT, "perception", dummy_handler)

    # Unknown capability name should raise ValueError
    with pytest.raises(ValueError, match="Unknown capability"):
        registry.register("invalid.capability", "engine", dummy_handler)



def test_plan_models():
    step = PlanStep(
        order=1,
        capability=PERCEPTION_STRUCTURE_INPUT,
        description="Step 1",
    )
    assert step.status == StepStatus.PENDING

    plan = Plan(
        task_id="task-1",
        goal="Test goal",
        steps=[step],
        status=PlanStatus.ACTIVE,
    )
    assert plan.version == 1
    assert plan.can_replan() is True
    assert plan.get_current_step() == step

    step.status = StepStatus.COMPLETED
    assert plan.get_current_step() is None
    assert len(plan.get_completed_steps()) == 1
