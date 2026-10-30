"""Plan and replan models for the Ring 1 Planning Engine.

Plans are versioned, step-based structures that describe how to accomplish a
task using registered capabilities. The Planning Engine creates and revises
plans; engines execute their own capabilities.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PlanStatus(str, Enum):
    """Overall plan lifecycle status."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED_FOR_CLARIFICATION = "paused_for_clarification"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Individual step execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"
    BLOCKED = "blocked"


class ReplanReasonCode(str, Enum):
    """Standard reason codes for requesting a replan."""

    MISSING_PREREQUISITE = "missing_prerequisite"
    CONTEXT_INSUFFICIENT = "context_insufficient"
    CAPABILITY_FAILED = "capability_failed"
    UNEXPECTED_RESULT = "unexpected_result"
    SCOPE_CHANGE = "scope_change"
    TIMEOUT = "timeout"
    AUTHORIZATION_DENIED = "authorization_denied"


# ---------------------------------------------------------------------------
# Plan step
# ---------------------------------------------------------------------------

class PlanStep(BaseModel):
    """A single step in an execution plan."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(default_factory=lambda: f"step-{uuid.uuid4().hex[:8]}")
    order: int
    capability: str
    description: str = ""
    preconditions: list[str] = Field(default_factory=list)
    expected_output: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    actual_result: Optional[dict[str, Any]] = None
    is_idempotent: bool = False
    is_safe_to_retry: bool = False
    failure_reason: Optional[str] = None
    skip_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

class Plan(BaseModel):
    """A versioned execution plan for a task.

    Plans are created by the Planning Engine and revised via replan requests.
    Each revision increments the version number and preserves the plan_id.
    """

    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:12]}")
    version: int = 1
    task_id: str
    goal: str
    steps: list[PlanStep] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    completion_criteria: str = ""
    stop_conditions: list[str] = Field(default_factory=list)
    allowed_capabilities: list[str] = Field(default_factory=list)
    context_ref: Optional[str] = None
    max_replans: int = Field(default=5, ge=0)
    replan_count: int = Field(default=0, ge=0)
    clarification_needed: Optional[str] = None

    def get_current_step(self) -> Optional[PlanStep]:
        """Return the first non-completed, non-skipped step."""
        for step in self.steps:
            if step.status in (StepStatus.PENDING, StepStatus.IN_PROGRESS, StepStatus.BLOCKED):
                return step
        return None

    def get_completed_steps(self) -> list[PlanStep]:
        """Return all completed steps."""
        return [s for s in self.steps if s.status == StepStatus.COMPLETED]

    def is_terminal(self) -> bool:
        """True if the plan has reached a final state."""
        return self.status in (
            PlanStatus.COMPLETED,
            PlanStatus.FAILED,
            PlanStatus.CANCELLED,
        )

    def can_replan(self) -> bool:
        """True if replanning is still allowed within configured limits."""
        return self.replan_count < self.max_replans and not self.is_terminal()


# ---------------------------------------------------------------------------
# Replan request (engine -> Planning Engine)
# ---------------------------------------------------------------------------

class ReplanRequest(BaseModel):
    """Typed request from an engine to the Planning Engine for plan revision.

    Includes the failed step, reason, evidence, and optional capability
    suggestions (which are treated as hints, not commands).
    """

    model_config = ConfigDict(extra="forbid")

    task_id: str
    plan_id: str
    plan_version: int
    requesting_engine: str
    failed_step_id: str
    expected_output: Optional[str] = None
    actual_result: Optional[dict[str, Any]] = None
    reason_code: ReplanReasonCode
    evidence: Optional[dict[str, Any]] = None
    context_ref: Optional[str] = None
    suggested_capabilities: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Replan response (Planning Engine -> requesting engine)
# ---------------------------------------------------------------------------

class ReplanResponse(BaseModel):
    """Result of a replan evaluation by the Planning Engine."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    new_version: int
    reason: str
    steps_retained: list[str] = Field(default_factory=list)
    steps_skipped: list[str] = Field(default_factory=list)
    steps_added: list[PlanStep] = Field(default_factory=list)
    resume_step_id: Optional[str] = None
    updated_preconditions: list[str] = Field(default_factory=list)
    clarification_needed: Optional[str] = None
    stop_conditions: list[str] = Field(default_factory=list)
    is_terminal: bool = False
    terminal_reason: Optional[str] = None
