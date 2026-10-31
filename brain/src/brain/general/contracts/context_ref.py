"""Context reference model for General Brain scope propagation.

A ContextRef carries the resolved scope identifiers (organization, domain,
case/scope, user) and a resolution status. It is attached to every mesh message
that touches context-sensitive data so that Memory and Retrieval engines
can enforce isolation in code.
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ResolutionStatus(str, Enum):
    """Outcome of a context resolution attempt."""

    RESOLVED = "resolved"
    EXPLICIT = "explicit"
    INFERRED = "inferred"
    AMBIGUOUS = "ambiguous"
    INSUFFICIENT_DATA = "insufficient_data"
    UNRESOLVED = "unresolved"
    FAILED = "failed"


class ContextRef(BaseModel):
    """Resolved context scope for a task or record.

    Downstream engines carry this reference to enforce data isolation.
    A ContextRef with status != RESOLVED / EXPLICIT must not be used for
    context-sensitive reads or writes without explicit handling.
    """

    model_config = ConfigDict(frozen=True)

    context_ref_id: str = Field(
        default_factory=lambda: f"ctx-{uuid.uuid4().hex[:12]}"
    )
    organization_id: Optional[str] = None
    domain_id: Optional[str] = None
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    user_id: Optional[str] = None
    resolution_status: ResolutionStatus = ResolutionStatus.INSUFFICIENT_DATA
    ambiguities: list[str] = Field(default_factory=list)
    scope_constraints: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_scope_and_case(cls, data: Any) -> Any:
        if isinstance(data, dict):
            scope = data.get("scope_id")
            case = data.get("case_id")
            if scope and not case:
                data["case_id"] = scope
            elif case and not scope:
                data["scope_id"] = case
        return data

    @property
    def effective_scope_id(self) -> Optional[str]:
        return self.scope_id or self.case_id

    @property
    def ref(self) -> str:
        """Alias for context_ref_id."""
        return self.context_ref_id

    @property
    def is_resolved(self) -> bool:
        return self.resolution_status in (
            ResolutionStatus.RESOLVED,
            ResolutionStatus.EXPLICIT,
            ResolutionStatus.INFERRED,
        )

    def to_ref_string(self) -> str:
        """Return the context_ref_id for propagation in mesh messages."""
        return self.context_ref_id
