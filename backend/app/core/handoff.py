"""Handoff Policy Engine for Ring 1 Capabilities.

Enforces strict peer-to-peer delegation boundaries, explicit transition allowlists,
cycle/loop detection, and maximum delegation depth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

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
)


class HandoffRejectionReason(str, Enum):
    UNKNOWN_CAPABILITY = "UNKNOWN_CAPABILITY"
    DISALLOWED_TRANSITION = "DISALLOWED_TRANSITION"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    MAX_DEPTH_EXCEEDED = "MAX_DEPTH_EXCEEDED"
    AUTONOMOUS_PLANNING_FORBIDDEN = "AUTONOMOUS_PLANNING_FORBIDDEN"


@dataclass(frozen=True)
class HandoffValidationResult:
    is_permitted: bool
    reason: Optional[HandoffRejectionReason] = None
    detail: Optional[str] = None


class HandoffPolicy:
    """Domain-blind policy engine governing capability transitions."""

    DEFAULT_MAX_DEPTH: int = 10

    # Explicit permitted transitions: (source_capability, target_capability)
    PERMITTED_TRANSITIONS: frozenset[tuple[str, str]] = frozenset({
        # Perception -> Observation
        (PERCEPTION_STRUCTURE_INPUT, OBSERVATION_RECORD_EVENT),
        
        # Observation -> Context, Retrieval, Memory
        (OBSERVATION_RECORD_EVENT, CONTEXT_RESOLVE),
        (OBSERVATION_RECORD_EVENT, RETRIEVAL_QUERY),
        (OBSERVATION_RECORD_EVENT, MEMORY_STORE_RECORD),
        
        # Context -> Retrieval, Memory
        (CONTEXT_RESOLVE, RETRIEVAL_QUERY),
        (CONTEXT_RESOLVE, MEMORY_STORE_RECORD),
        (CONTEXT_RESOLVE, MEMORY_GET_RECORD),
        
        # Retrieval -> Memory, Context
        (RETRIEVAL_QUERY, CONTEXT_RESOLVE),
        (RETRIEVAL_QUERY, MEMORY_GET_RECORD),
        
        # Memory -> Retrieval, Context
        (MEMORY_STORE_RECORD, RETRIEVAL_QUERY),
        (MEMORY_STORE_RECORD, CONTEXT_RESOLVE),
        (MEMORY_GET_RECORD, CONTEXT_RESOLVE),
        
        # External runtime entry points (None source) to any primary capability
        ("", PERCEPTION_STRUCTURE_INPUT),
        ("", OBSERVATION_RECORD_EVENT),
        ("", CONTEXT_RESOLVE),
        ("", MEMORY_STORE_RECORD),
        ("", MEMORY_GET_RECORD),
        ("", RETRIEVAL_QUERY),
        ("", PLANNING_CREATE_PLAN),
        ("", PLANNING_GET_PLAN_STATUS),
    })

    def __init__(self, max_depth: int = DEFAULT_MAX_DEPTH) -> None:
        self.max_depth = max_depth

    def validate_handoff(
        self,
        source_capability: Optional[str],
        target_capability: str,
        traversal_history: Optional[list[str]] = None,
    ) -> HandoffValidationResult:
        """Validate if a capability handoff is permitted under Ring 1 rules."""
        src = source_capability or ""
        history = traversal_history or []

        # 1. Target capability must be registered in Ring 1
        if target_capability not in ALL_CAPABILITIES:
            return HandoffValidationResult(
                is_permitted=False,
                reason=HandoffRejectionReason.UNKNOWN_CAPABILITY,
                detail=f"Target capability '{target_capability}' is not in ALL_CAPABILITIES.",
            )

        # 2. Section 2.3: Observation cannot autonomously initiate planning
        if src == OBSERVATION_RECORD_EVENT and target_capability in (
            PLANNING_CREATE_PLAN,
            PLANNING_REQUEST_REPLAN,
        ):
            return HandoffValidationResult(
                is_permitted=False,
                reason=HandoffRejectionReason.AUTONOMOUS_PLANNING_FORBIDDEN,
                detail="Observation Engine cannot autonomously initiate planning.",
            )

        # 3. Direct self-loop check
        if target_capability == src:
            return HandoffValidationResult(
                is_permitted=False,
                reason=HandoffRejectionReason.CYCLE_DETECTED,
                detail=f"Direct self-loop detected for capability '{target_capability}'.",
            )

        # 4. Check delegation depth limit
        if len(history) >= self.max_depth:
            return HandoffValidationResult(
                is_permitted=False,
                reason=HandoffRejectionReason.MAX_DEPTH_EXCEEDED,
                detail=f"Maximum handoff depth of {self.max_depth} exceeded.",
            )

        # 5. Cycle detection: repeated cycles in history
        if history.count(target_capability) >= 2:
            return HandoffValidationResult(
                is_permitted=False,
                reason=HandoffRejectionReason.CYCLE_DETECTED,
                detail=f"Cycle detected: capability '{target_capability}' called multiple times in history.",
            )

        # 6. Check transition allowlist
        if (src, target_capability) not in self.PERMITTED_TRANSITIONS:
            # Special case: replan requests can be triggered by runtime when handling failures
            if target_capability == PLANNING_REQUEST_REPLAN and src in ALL_CAPABILITIES:
                pass  # Permitted advisory failure recovery
            else:
                return HandoffValidationResult(
                    is_permitted=False,
                    reason=HandoffRejectionReason.DISALLOWED_TRANSITION,
                    detail=f"Transition from '{src or 'EXTERNAL'}' to '{target_capability}' is not permitted.",
                )

        return HandoffValidationResult(is_permitted=True)
