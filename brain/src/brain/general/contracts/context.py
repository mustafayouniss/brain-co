"""Authoritative BrainContext contract for General Brain.

Immutable, typed execution context for all General Brain engines and extensions.
Derived strictly from server-side authenticated context and deployment configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass(frozen=True)
class BrainContext:
    """Immutable, authenticated execution context for all General Brain engines.
    
    Downstream engines consume this validated context rather than parsing headers
    or trusting raw payload identifiers.
    """

    organization_id: str
    user_id: Optional[str] = None
    case_id: Optional[str] = None
    scope_id: Optional[str] = None
    domain_id: str = "general"
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    role: str = "employee"
    validation_authority: bool = False
    permissions: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.scope_id and not self.case_id:
            object.__setattr__(self, "case_id", self.scope_id)
        elif self.case_id and not self.scope_id:
            object.__setattr__(self, "scope_id", self.case_id)

    @property
    def effective_scope_id(self) -> Optional[str]:
        return self.scope_id or self.case_id

    def with_task(self, task_id: str, correlation_id: Optional[str] = None) -> BrainContext:
        """Create a child execution context bound to a specific task identity."""
        return BrainContext(
            organization_id=self.organization_id,
            user_id=self.user_id,
            case_id=self.case_id,
            scope_id=self.scope_id,
            domain_id=self.domain_id,
            task_id=task_id,
            correlation_id=correlation_id or self.correlation_id or str(uuid.uuid4()),
            role=self.role,
            validation_authority=self.validation_authority,
            permissions=self.permissions,
        )

    def with_case(self, case_id: str) -> BrainContext:
        """Create a child context bound to a validated case boundary."""
        return BrainContext(
            organization_id=self.organization_id,
            user_id=self.user_id,
            case_id=case_id,
            scope_id=case_id,
            domain_id=self.domain_id,
            task_id=self.task_id,
            correlation_id=self.correlation_id,
            role=self.role,
            validation_authority=self.validation_authority,
            permissions=self.permissions,
        )

    def with_scope(self, scope_id: str, domain_id: Optional[str] = None) -> BrainContext:
        """Create a child execution context bound to a specific domain scope."""
        return BrainContext(
            organization_id=self.organization_id,
            user_id=self.user_id,
            case_id=scope_id,
            scope_id=scope_id,
            domain_id=domain_id or self.domain_id,
            task_id=self.task_id,
            correlation_id=self.correlation_id,
            role=self.role,
            validation_authority=self.validation_authority,
            permissions=self.permissions,
        )
