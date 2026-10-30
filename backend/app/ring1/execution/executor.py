"""Plan Step Executor for Ring 1.

Responsible for executing validated Plan steps across the capability mesh via MeshRouter.
Maintains clear separation of concerns (per ADR-008):
- PlanningEngine creates and revises plans.
- PlanStepExecutor coordinates step execution across engines through MeshRouter.
- Individual engines execute their own capabilities.

Status transitions:
- Step marked COMPLETED only after genuine successful capability response.
- Step marked FAILED upon execution error, unhandled exception, or non-success status.
- Automatically captures actual_result, error details, and execution duration.
"""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncGenerator, Callable, Optional

from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.contracts.context_ref import ContextRef
from app.ring1.contracts.envelopes import (
    DelegationConstraints,
    MeshRequest,
    MeshResponse,
    ResultStatus,
)
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import (
    Plan,
    PlanStatus,
    PlanStep,
    ReplanReasonCode,
    StepStatus,
)
from app.ring1.mesh.router import MeshRouter

logger = logging.getLogger("ring1.executor")


class PlanStepExecutor:
    """Minimal, deterministic Plan Step Executor for Ring 1."""

    def __init__(
        self,
        router: MeshRouter,
        registry: CapabilityRegistry,
        *,
        fault_injector: Optional[
            Callable[[PlanStep, MeshRequest], Optional[MeshRequest]]
        ] = None,
    ) -> None:
        self.router = router
        self.registry = registry
        self.fault_injector = fault_injector

    async def execute_step(
        self,
        plan: Plan,
        step: PlanStep,
        context_ref: Optional[ContextRef] = None,
        custom_payload: Optional[dict[str, Any]] = None,
    ) -> tuple[MeshResponse, StepStatus]:
        """Execute a single plan step through the mesh router.

        Validates capability registration, builds a typed MeshRequest, applies any
        explicit test fault injection at the execution boundary, and records the real
        runtime outcome on the PlanStep.
        """
        # 1. Capability registry validation
        if not self.registry.is_registered(step.capability):
            step.status = StepStatus.FAILED
            step.actual_result = {
                "error": f"Capability '{step.capability}' is not registered in CapabilityRegistry.",
                "code": EngineErrorCode.CAPABILITY_NOT_FOUND.value,
            }
            error_resp = MeshResponse.failure(
                request=MeshRequest(
                    sender_engine="plan_executor",
                    recipient_capability=step.capability,
                    payload={},
                ),
                sender_engine="plan_executor",
                status=ResultStatus.FAILED,
                errors=[
                    {
                        "code": EngineErrorCode.CAPABILITY_NOT_FOUND.value,
                        "message": f"Unregistered capability '{step.capability}'",
                        "engine": "plan_executor",
                    }
                ],
            )
            return error_resp, StepStatus.FAILED

        # 2. Prerequisite validation (depends_on)
        for dep_id in step.depends_on:
            dep_step = next((s for s in plan.steps if s.step_id == dep_id), None)
            if dep_step is None:
                step.status = StepStatus.BLOCKED
                err_msg = f"Prerequisite step '{dep_id}' was not found in plan."
                step.actual_result = {
                    "error": err_msg,
                    "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                }
                error_resp = MeshResponse.failure(
                    request=MeshRequest(
                        sender_engine="plan_executor",
                        recipient_capability=step.capability,
                        payload={},
                    ),
                    sender_engine="plan_executor",
                    status=ResultStatus.FAILED,
                    errors=[
                        {
                            "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                            "message": err_msg,
                            "engine": "plan_executor",
                        }
                    ],
                )
                return error_resp, StepStatus.BLOCKED

            if dep_step.status != StepStatus.COMPLETED:
                step.status = StepStatus.BLOCKED
                err_msg = (
                    f"Prerequisite step '{dep_id}' ({dep_step.capability}) is not completed "
                    f"(current status: {dep_step.status.value})."
                )
                step.actual_result = {
                    "error": err_msg,
                    "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                    "dependency_step_id": dep_id,
                    "dependency_status": dep_step.status.value,
                }
                error_resp = MeshResponse.failure(
                    request=MeshRequest(
                        sender_engine="plan_executor",
                        recipient_capability=step.capability,
                        payload={},
                    ),
                    sender_engine="plan_executor",
                    status=ResultStatus.FAILED,
                    errors=[
                        {
                            "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                            "message": err_msg,
                            "engine": "plan_executor",
                        }
                    ],
                )
                return error_resp, StepStatus.BLOCKED

        # 3. Derive request payload based on step capability and plan context
        step_payload = self._build_step_payload(plan, step, context_ref, custom_payload)

        # 4. Construct typed request
        request = MeshRequest(
            task_id=plan.task_id,
            plan_version=plan.version,
            sender_engine="plan_executor",
            recipient_capability=step.capability,
            context_ref=context_ref,
            payload=step_payload,
            constraints=DelegationConstraints(max_delegations_remaining=3),
        )

        # 5. Controlled test fault injection at the execution boundary
        if self.fault_injector is not None:
            injected_req = self.fault_injector(step, request)
            if injected_req is not None:
                request = injected_req

        # 6. Dispatch via real MeshRouter
        step.status = StepStatus.IN_PROGRESS
        response = await self.router.dispatch(request)

        # 7. Evaluate genuine runtime outcome
        if response.status == ResultStatus.SUCCESS:
            step.status = StepStatus.COMPLETED
            step.actual_result = response.payload
        else:
            step.status = StepStatus.FAILED
            step.actual_result = {
                "status": response.status.value,
                "errors": [e.model_dump() for e in response.errors] if response.errors else [],
            }

        return response, step.status

    async def execute_plan(
        self,
        plan: Plan,
        context_ref: Optional[ContextRef] = None,
        max_steps: Optional[int] = None,
        step_payloads: Optional[dict[str, dict[str, Any]]] = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute all remaining pending steps in a plan, yielding execution events."""
        plan.status = PlanStatus.ACTIVE
        steps_executed = 0

        for step in plan.steps:
            if max_steps is not None and steps_executed >= max_steps:
                break

            if step.status == StepStatus.COMPLETED:
                # Retained step from previous version
                yield {
                    "event_type": "step_retained",
                    "step_id": step.step_id,
                    "order": step.order,
                    "capability": step.capability,
                    "status": "completed",
                    "plan_version": plan.version,
                }
                continue

            if step.status in (StepStatus.FAILED, StepStatus.SKIPPED, StepStatus.BLOCKED):
                continue

            # Execute pending step
            custom_payload = None
            if step_payloads:
                custom_payload = step_payloads.get(step.step_id) or step_payloads.get(step.capability)

            t0 = time.perf_counter()
            yield {
                "event_type": "step_started",
                "step_id": step.step_id,
                "order": step.order,
                "capability": step.capability,
                "status": "in_progress",
                "plan_version": plan.version,
            }

            resp, final_status = await self.execute_step(plan, step, context_ref, custom_payload=custom_payload)
            duration_ms = round((time.perf_counter() - t0) * 1000, 2)
            steps_executed += 1

            if final_status == StepStatus.COMPLETED:
                yield {
                    "event_type": "step_completed",
                    "step_id": step.step_id,
                    "order": step.order,
                    "capability": step.capability,
                    "status": "completed",
                    "duration_ms": duration_ms,
                    "plan_version": plan.version,
                    "result": step.actual_result,
                    "response_envelope": resp.model_dump(mode="json"),
                }
            elif final_status == StepStatus.BLOCKED:
                yield {
                    "event_type": "step_blocked",
                    "step_id": step.step_id,
                    "order": step.order,
                    "capability": step.capability,
                    "status": "blocked",
                    "duration_ms": duration_ms,
                    "plan_version": plan.version,
                    "result": step.actual_result,
                    "response_envelope": resp.model_dump(mode="json"),
                }
                # Blocked prerequisite halts execution
                break
            else:
                yield {
                    "event_type": "step_failed",
                    "step_id": step.step_id,
                    "order": step.order,
                    "capability": step.capability,
                    "status": "failed",
                    "duration_ms": duration_ms,
                    "plan_version": plan.version,
                    "result": step.actual_result,
                    "response_envelope": resp.model_dump(mode="json"),
                }
                # Block downstream dependent steps
                for downstream in plan.steps:
                    if step.step_id in downstream.depends_on and downstream.status == StepStatus.PENDING:
                        downstream.status = StepStatus.BLOCKED
                        downstream.actual_result = {
                            "error": f"Blocked because prerequisite '{step.step_id}' ({step.capability}) failed.",
                            "code": EngineErrorCode.MISSING_PREREQUISITE.value,
                        }
                        yield {
                            "event_type": "step_blocked",
                            "step_id": downstream.step_id,
                            "order": downstream.order,
                            "capability": downstream.capability,
                            "status": "blocked",
                            "plan_version": plan.version,
                            "result": downstream.actual_result,
                        }
                if not plan.can_replan():
                    plan.status = PlanStatus.FAILED
                break

        # Check if all active steps completed
        # Steps that failed in an earlier version are considered resolved if superseded by a completed recovery step
        unresolved_steps = [
            s for s in plan.steps
            if s.status not in (StepStatus.COMPLETED, StepStatus.SKIPPED)
            and not (s.status == StepStatus.FAILED and any(rec.order > s.order and rec.status == StepStatus.COMPLETED for rec in plan.steps))
        ]
        if plan.steps and not unresolved_steps:
            plan.status = PlanStatus.COMPLETED

    def _build_step_payload(
        self,
        plan: Plan,
        step: PlanStep,
        context_ref: Optional[ContextRef],
        custom: Optional[dict[str, Any]],
    ) -> dict[str, Any]:
        """Construct realistic, capability-specific payload for step execution."""
        if custom:
            return custom

        cap = step.capability
        if cap == "perception.structure_input":
            return {
                "raw_content": plan.goal,
                "source_type": "text",
            }
        elif cap == "context.resolve":
            return {
                "context_hint": {
                    "goal": plan.goal,
                    "organization_id": context_ref.organization_id if context_ref else "org-default",
                    "case_id": context_ref.case_id if context_ref else "case-default",
                    "domain_id": context_ref.domain_id if context_ref else "general",
                }
            }
        elif cap == "retrieval.query":
            return {
                "query": plan.goal,
                "case_id": context_ref.case_id if context_ref else None,
                "top_k": 5,
            }
        elif cap == "memory.store_record":
            return {
                "record_type": "plan_checkpoint",
                "case_id": context_ref.case_id if context_ref else None,
                "payload": {"goal": plan.goal, "step_id": step.step_id},
            }
        elif cap == "observation.record_event":
            return {
                "event_type": "plan_step_executing",
                "source": "plan_executor",
                "payload": {"plan_id": plan.plan_id, "step_id": step.step_id},
            }

        return {"goal": plan.goal, "step_id": step.step_id}
