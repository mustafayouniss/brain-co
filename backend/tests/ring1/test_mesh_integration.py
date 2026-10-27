"""Tests for inter-engine mesh routing, peer delegation, and traceability."""

import pytest

from app.ring1.contracts.capabilities import (
    CONTEXT_RESOLVE,
    MEMORY_STORE_RECORD,
    OBSERVATION_RECORD_EVENT,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    RETRIEVAL_QUERY,
)
from app.ring1.contracts.context_ref import ContextRef, ResolutionStatus
from app.ring1.contracts.envelopes import (
    PROTOCOL_VERSION,
    DelegationConstraints,
    MeshRequest,
    ResultStatus,
)

from app.ring1.contracts.errors import EngineErrorCode


@pytest.mark.asyncio
async def test_mesh_router_dispatch_to_registered_capability(ring1_mesh):
    router = ring1_mesh["router"]
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": '{"event": "start"}', "input_type": "json"},
    )
    resp = await router.dispatch(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.sender_engine == "perception"
    assert resp.correlation_id == req.message_id
    assert resp.task_id == req.task_id


@pytest.mark.asyncio
async def test_mesh_router_unregistered_capability(ring1_mesh):
    router = ring1_mesh["router"]
    # Even if bypassing validation, registry should not find it
    req = MeshRequest.model_construct(
        protocol_version=PROTOCOL_VERSION,
        message_id="msg-test",
        sender_engine="client",
        recipient_capability="unknown.capability",
        payload={},
        constraints=DelegationConstraints(),
    )

    resp = await router.dispatch(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.CAPABILITY_NOT_FOUND.value


@pytest.mark.asyncio
async def test_mesh_delegation_trace_propagation(ring1_mesh):
    router = ring1_mesh["router"]
    perception = ring1_mesh["perception"]

    parent_req = MeshRequest(
        task_id="task-root-123",
        trace_id="trace-root-456",
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        context_ref=ContextRef(
            organization_id="org-1",
            case_id="case-100",
            status=ResolutionStatus.EXPLICIT,
        ),
        payload={"raw_content": "test payload"},
        constraints=DelegationConstraints(max_delegations_remaining=3),
    )

    # Perception delegates to Memory via _delegate
    child_resp = await perception._delegate(
        parent_request=parent_req,
        recipient_capability=MEMORY_STORE_RECORD,
        payload={"record_type": "parsed_doc", "payload": {"status": "done"}},
    )

    assert child_resp.status == ResultStatus.SUCCESS
    assert child_resp.sender_engine == "memory"
    assert child_resp.task_id == "task-root-123"
    assert child_resp.trace_id == "trace-root-456"


@pytest.mark.asyncio
async def test_mesh_delegation_depth_exhaustion(ring1_mesh):
    router = ring1_mesh["router"]

    # Request with 0 delegations remaining
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PERCEPTION_STRUCTURE_INPUT,
        payload={"raw_content": "hello"},
        constraints=DelegationConstraints(max_delegations_remaining=0),
    )

    resp = await router.dispatch(req)
    assert resp.status == ResultStatus.FAILED
    assert resp.errors[0].code == EngineErrorCode.DELEGATION_DEPTH_EXCEEDED.value
