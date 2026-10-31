"""Tests for Planning Engine."""

import pytest

from app.ring1.contracts.capabilities import (
    ALL_CAPABILITIES,
    PLANNING_CREATE_PLAN,
    PLANNING_GET_PLAN_STATUS,
    PLANNING_REQUEST_REPLAN,
)
from app.ring1.contracts.envelopes import MeshRequest, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import PlanStatus, ReplanReasonCode
from app.ring1.engines.planning import PlanningEngine


@pytest.mark.asyncio
async def test_planning_create_plan(fake_llm_service):
    engine = PlanningEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        payload={"goal": "Analyze uploaded contracts for compliance breach", "max_replans": 2},
    )
    resp = await engine.handle_create_plan(req)
    assert resp.status == ResultStatus.SUCCESS
    assert resp.payload["version"] == 1
    assert resp.payload["max_replans"] == 2
    assert resp.payload["step_count"] > 0

    # Ensure every single step capability is in ALL_CAPABILITIES
    for step in resp.payload["steps"]:
        assert step["capability"] in ALL_CAPABILITIES


@pytest.mark.asyncio
async def test_planning_create_plan_missing_goal(fake_llm_service):
    engine = PlanningEngine(llm_service=fake_llm_service)
    req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        payload={},
    )
    resp = await engine.handle_create_plan(req)
    assert resp.status == ResultStatus.INVALID_REQUEST
    assert resp.errors[0].code == EngineErrorCode.INVALID_PAYLOAD.value


@pytest.mark.asyncio
async def test_planning_replan_lifecycle(fake_llm_service):
    engine = PlanningEngine(llm_service=fake_llm_service)

    # 1. Create plan
    create_req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        payload={"goal": "Prepare trial evidence bundle", "max_replans": 2},
    )
    create_resp = await engine.handle_create_plan(create_req)
    plan_id = create_resp.payload["plan_id"]
    failed_step_id = create_resp.payload["steps"][0]["step_id"]

    # 2. First replan
    replan_req1 = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        payload={
            "plan_id": plan_id,
            "failed_step_id": failed_step_id,
            "reason_code": ReplanReasonCode.CONTEXT_INSUFFICIENT.value,
        },
    )
    replan_resp1 = await engine.handle_request_replan(replan_req1)
    assert replan_resp1.status == ResultStatus.SUCCESS
    assert replan_resp1.payload["new_version"] == 2

    # 3. Second replan (hits max_replans limit = 2)
    replan_req2 = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        payload={
            "plan_id": plan_id,
            "failed_step_id": failed_step_id,
            "reason_code": ReplanReasonCode.CAPABILITY_FAILED.value,
        },
    )
    replan_resp2 = await engine.handle_request_replan(replan_req2)
    assert replan_resp2.status == ResultStatus.SUCCESS
    assert replan_resp2.payload["new_version"] == 3

    # 4. Third replan (MUST fail due to bounded replanning limit)
    replan_req3 = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_REQUEST_REPLAN,
        payload={
            "plan_id": plan_id,
            "failed_step_id": failed_step_id,
            "reason_code": ReplanReasonCode.CAPABILITY_FAILED.value,
        },
    )
    replan_resp3 = await engine.handle_request_replan(replan_req3)
    assert replan_resp3.status == ResultStatus.FAILED
    assert replan_resp3.errors[0].code == EngineErrorCode.REPLAN_LIMIT_EXCEEDED.value


@pytest.mark.asyncio
async def test_planning_get_plan_status(fake_llm_service):
    engine = PlanningEngine(llm_service=fake_llm_service)
    create_req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        payload={"goal": "Audit filing documents"},
    )
    create_resp = await engine.handle_create_plan(create_req)
    plan_id = create_resp.payload["plan_id"]

    status_req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_GET_PLAN_STATUS,
        payload={"plan_id": plan_id},
    )
    status_resp = await engine.handle_get_plan_status(status_req)
    assert status_resp.status == ResultStatus.SUCCESS
    assert status_resp.payload["plan_id"] == plan_id
    assert status_resp.payload["status"] == PlanStatus.ACTIVE.value


@pytest.mark.asyncio
async def test_planning_in_memory_ephemerality_restart_behavior(fake_llm_service):
    """Ring 1 plans are in-memory by design (PostgreSQL plan persistence is deferred to higher rings).

    Proves that a fresh PlanningEngine instance does not retain plans from previous processes,
    making process restart behavior explicit.
    """
    engine_process_1 = PlanningEngine(llm_service=fake_llm_service)
    create_req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_CREATE_PLAN,
        payload={"goal": "Examine session-bound lifecycle"},
    )
    create_resp = await engine_process_1.handle_create_plan(create_req)
    plan_id = create_resp.payload["plan_id"]

    # Process restart: new engine instance
    engine_process_2 = PlanningEngine(llm_service=fake_llm_service)
    status_req = MeshRequest(
        sender_engine="client",
        recipient_capability=PLANNING_GET_PLAN_STATUS,
        payload={"plan_id": plan_id},
    )
    status_resp = await engine_process_2.handle_get_plan_status(status_req)
    assert status_resp.status == ResultStatus.FAILED
    assert status_resp.errors[0].code == EngineErrorCode.DATA_NOT_FOUND.value
