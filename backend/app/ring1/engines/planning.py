"""Planning Engine — creates, tracks, and boundedly revises multi-step execution plans.

Deterministic Core:
- Generates structured, versioned execution plans using registered Ring 1 capabilities only
- Validates all plan steps against ALL_CAPABILITIES allowlist
- Tracks plan lifecycle: DRAFT -> ACTIVE -> COMPLETED / FAILED / PAUSED
- Enforces bounded replanning (max_replans limit, reject if exceeded)
- Validates replan requests with standard reason codes (ReplanReasonCode)
- Preserves plan history and versions across revisions

Intelligence Layer:
- Decomposes unstructured goals into sequenced capability steps via LLM
- Validates LLM proposed steps against strict capability allowlist before accepting
- Deterministic fallback if LLM is unavailable or produces invalid steps

Must not: execute capability steps (engines execute their own capabilities),
invent unregistered capabilities, loop infinitely on replanning.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from app.ring1.contracts.capabilities import (
    ALL_CAPABILITIES,
    CONTEXT_RESOLVE,
    MEMORY_STORE_RECORD,
    PERCEPTION_STRUCTURE_INPUT,
    PLANNING_CREATE_PLAN,
    PLANNING_GET_PLAN_STATUS,
    PLANNING_REQUEST_REPLAN,
    RETRIEVAL_QUERY,
    CapabilityRegistry,
)
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.plan_models import (
    Plan,
    PlanStatus,
    PlanStep,
    ReplanReasonCode,
    ReplanRequest,
    ReplanResponse,
    StepStatus,
)
from app.ring1.engines.base import BaseEngine


class PlanningEngine(BaseEngine):
    """Ring 1 Planning Engine [GB].

    Responsible for creating and revising structured plans. Operates strictly within
    the capability mesh by assigning work to registered capabilities.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._plans: dict[str, Plan] = {}

    @property
    def engine_name(self) -> str:
        return "planning"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            PLANNING_CREATE_PLAN,
            self.engine_name,
            self.handle_create_plan,
            description="Create a structured, capability-aligned execution plan for a goal.",
        )
        registry.register(
            PLANNING_REQUEST_REPLAN,
            self.engine_name,
            self.handle_request_replan,
            description="Request a bounded plan revision following a step failure or scope change.",
        )
        registry.register(
            PLANNING_GET_PLAN_STATUS,
            self.engine_name,
            self.handle_get_plan_status,
            description="Retrieve the current status, version, and steps of an active plan.",
        )

    # -----------------------------------------------------------------
    # Capability: planning.create_plan
    # -----------------------------------------------------------------

    async def handle_create_plan(self, request: MeshRequest) -> MeshResponse:
        """Create a versioned execution plan for a task goal.

        Payload expected:
        - goal: str (required, the high-level objective)
        - task_id: str (optional, defaults to request.task_id)
        - max_replans: int (optional, default 3)
        - stop_conditions: list[str] (optional)
        - completion_criteria: str (optional)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        goal = (request.payload.get("goal") or "").strip()
        if not goal:
            return self._error(
                request,
                ResultStatus.INVALID_REQUEST,
                EngineErrorCode.INVALID_PAYLOAD,
                "Missing required 'goal' in plan creation request.",
            )

        task_id = request.payload.get("task_id") or request.task_id
        max_replans = int(request.payload.get("max_replans", 3))
        stop_conditions = request.payload.get("stop_conditions", [])
        completion_criteria = request.payload.get(
            "completion_criteria", f"Goal achieved: {goal}"
        )
        context_ref_str = request.context_ref.ref if request.context_ref else None

        # Generate steps (LLM intelligence layer with deterministic fallback)
        steps = await self._generate_plan_steps(goal)

        plan = Plan(
            task_id=task_id,
            goal=goal,
            steps=steps,
            status=PlanStatus.ACTIVE,
            completion_criteria=completion_criteria,
            stop_conditions=stop_conditions,
            allowed_capabilities=list(ALL_CAPABILITIES),
            context_ref=context_ref_str,
            max_replans=max_replans,
            replan_count=0,
        )

        self._plans[plan.plan_id] = plan

        return self._success(
            request,
            {
                "plan_id": plan.plan_id,
                "version": plan.version,
                "status": plan.status.value,
                "goal": plan.goal,
                "step_count": len(plan.steps),
                "steps": [s.model_dump() for s in plan.steps],
                "max_replans": plan.max_replans,
                "replan_count": plan.replan_count,
            },
            context_ref=context_ref_str,
        )

    # -----------------------------------------------------------------
    # Capability: planning.request_replan
    # -----------------------------------------------------------------

    async def handle_request_replan(self, request: MeshRequest) -> MeshResponse:
        """Handle a replan request when a step fails or unexpected conditions arise.

        Payload expected:
        - plan_id: str (required)
        - failed_step_id: str (required)
        - reason_code: str (one of ReplanReasonCode)
        - expected_output: str (optional)
        - actual_result: dict (optional)
        - suggested_capabilities: list[str] (optional hints)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        plan_id = request.payload.get("plan_id")
        if not plan_id or plan_id not in self._plans:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.DATA_NOT_FOUND,
                f"Plan '{plan_id}' not found.",
            )

        plan = self._plans[plan_id]

        # Check bounded replanning limit
        if not plan.can_replan():
            plan.status = PlanStatus.FAILED
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.REPLAN_LIMIT_EXCEEDED,
                f"Replan limit ({plan.max_replans}) exceeded for plan '{plan_id}'. Marking plan as FAILED.",
                details={
                    "plan_id": plan_id,
                    "replan_count": plan.replan_count,
                    "max_replans": plan.max_replans,
                },
            )

        failed_step_id = request.payload.get("failed_step_id")
        raw_reason = request.payload.get("reason_code", ReplanReasonCode.CAPABILITY_FAILED.value)
        try:
            reason_code = ReplanReasonCode(raw_reason)
        except ValueError:
            reason_code = ReplanReasonCode.CAPABILITY_FAILED

        # Increment version and count
        plan.version += 1
        plan.replan_count += 1

        # Mark failed step
        retained_step_ids = []
        for step in plan.steps:
            if step.step_id == failed_step_id:
                step.status = StepStatus.FAILED
                step.actual_result = request.payload.get("actual_result")
            elif step.status == StepStatus.COMPLETED:
                retained_step_ids.append(step.step_id)

        # Generate recovery steps
        recovery_steps = self._build_recovery_steps(
            plan=plan,
            failed_step_id=failed_step_id,
            reason_code=reason_code,
            suggested=request.payload.get("suggested_capabilities", []),
        )

        # Append recovery steps to plan
        max_order = max((s.order for s in plan.steps), default=0)
        for idx, step in enumerate(recovery_steps, start=max_order + 1):
            step.order = idx
            plan.steps.append(step)

        replan_response = ReplanResponse(
            plan_id=plan.plan_id,
            new_version=plan.version,
            reason=f"Replan triggered by {reason_code.value} on step {failed_step_id}",
            steps_retained=retained_step_ids,
            steps_skipped=[],
            steps_added=recovery_steps,
            resume_step_id=recovery_steps[0].step_id if recovery_steps else None,
            is_terminal=False,
        )

        return self._success(
            request,
            replan_response.model_dump(),
            context_ref=plan.context_ref,
        )

    # -----------------------------------------------------------------
    # Capability: planning.get_plan_status
    # -----------------------------------------------------------------

    async def handle_get_plan_status(self, request: MeshRequest) -> MeshResponse:
        """Get the current state and steps of an active plan.

        Payload expected:
        - plan_id: str (required)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        plan_id = request.payload.get("plan_id")
        if not plan_id or plan_id not in self._plans:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.DATA_NOT_FOUND,
                f"Plan '{plan_id}' not found.",
            )

        plan = self._plans[plan_id]
        current_step = plan.get_current_step()

        return self._success(
            request,
            {
                "plan_id": plan.plan_id,
                "version": plan.version,
                "status": plan.status.value,
                "goal": plan.goal,
                "replan_count": plan.replan_count,
                "max_replans": plan.max_replans,
                "current_step_id": current_step.step_id if current_step else None,
                "completed_steps": len(plan.get_completed_steps()),
                "total_steps": len(plan.steps),
                "steps": [s.model_dump() for s in plan.steps],
            },
            context_ref=plan.context_ref,
        )

    # -----------------------------------------------------------------
    # Intelligence Layer: step generation
    # -----------------------------------------------------------------

    async def _generate_plan_steps(self, goal: str) -> list[PlanStep]:
        """Generate structured capability steps for a goal using LLM, or fallback."""
        if self._llm_service:
            prompt = (
                "You are an AI planner for Ring 1 General Brain. "
                "Decompose the following user goal into 2 to 4 sequential steps. "
                "Each step MUST use ONLY one of these registered capabilities: "
                f"{', '.join(sorted(ALL_CAPABILITIES))}. "
                "Return a JSON array of objects with keys: "
                "'order' (int), 'capability' (str), 'description' (str), 'expected_output' (str)."
            )
            raw = await self._call_llm_json(prompt, goal)
            if isinstance(raw, list):
                valid_steps: list[PlanStep] = []
                for idx, item in enumerate(raw, start=1):
                    cap = item.get("capability", "")
                    if cap in ALL_CAPABILITIES:
                        valid_steps.append(
                            PlanStep(
                                order=idx,
                                capability=cap,
                                description=item.get("description", f"Step for {cap}"),
                                expected_output=item.get("expected_output"),
                                status=StepStatus.PENDING,
                            )
                        )
                if valid_steps:
                    return valid_steps

        # Deterministic fallback plan sequence
        return self._default_plan_steps(goal)

    def _default_plan_steps(self, goal: str) -> list[PlanStep]:
        """Deterministic fallback: standard 3-step pipeline."""
        return [
            PlanStep(
                order=1,
                capability=PERCEPTION_STRUCTURE_INPUT,
                description="Structure and normalize initial goal and context inputs.",
                expected_output="Structured representation of task input.",
                status=StepStatus.PENDING,
            ),
            PlanStep(
                order=2,
                capability=CONTEXT_RESOLVE,
                description="Resolve contextual boundaries and permissions.",
                expected_output="Resolved ContextRef with valid case_id.",
                status=StepStatus.PENDING,
            ),
            PlanStep(
                order=3,
                capability=RETRIEVAL_QUERY,
                description="Retrieve relevant case records or evidence.",
                expected_output="Relevant contextual records.",
                status=StepStatus.PENDING,
            ),
            PlanStep(
                order=4,
                capability=MEMORY_STORE_RECORD,
                description="Persist task results to memory.",
                expected_output="Record ID of saved result.",
                status=StepStatus.PENDING,
            ),
        ]

    def _build_recovery_steps(
        self,
        plan: Plan,
        failed_step_id: str,
        reason_code: ReplanReasonCode,
        suggested: list[str],
    ) -> list[PlanStep]:
        """Build deterministic recovery steps based on failure reason."""
        # Use valid suggested capabilities if provided
        filtered_suggestions = [c for c in suggested if c in ALL_CAPABILITIES]
        if filtered_suggestions:
            return [
                PlanStep(
                    order=1,
                    capability=cap,
                    description=f"Alternative step recovering from {reason_code.value}",
                    expected_output=f"Output from fallback capability {cap}",
                    status=StepStatus.PENDING,
                )
                for cap in filtered_suggestions
            ]

        if reason_code == ReplanReasonCode.CONTEXT_INSUFFICIENT:
            return [
                PlanStep(
                    order=1,
                    capability=CONTEXT_RESOLVE,
                    description="Re-resolve context with updated inputs.",
                    expected_output="Fully resolved ContextRef.",
                    status=StepStatus.PENDING,
                )
            ]

        # Default recovery: attempt context retrieval or perception refresh
        return [
            PlanStep(
                order=1,
                capability=RETRIEVAL_QUERY,
                description=f"Retrieve supplementary context after step {failed_step_id} failure.",
                expected_output="Supplementary context records.",
                status=StepStatus.PENDING,
            )
        ]
