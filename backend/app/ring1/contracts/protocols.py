"""Core Engine Protocols and Result Contracts for Ring 1.

Every Ring 1 engine adheres to a pure Python Protocol with decoupled transport,
explicit ownership boundaries, and dependency inversion.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable
import uuid
from uuid import UUID

from pydantic import BaseModel, Field

from app.core.context import BrainContext


class EngineResult(BaseModel):
    """Normalized, transport-independent output from an engine step."""

    data: dict[str, Any] = Field(default_factory=dict)
    proposed_destination: Optional[str] = None
    proposed_capability: Optional[str] = None
    proposed_payload: Optional[dict[str, Any]] = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    is_terminal: bool = False
    error: Optional[dict[str, Any]] = None


class ObservationFeedResult(BaseModel):
    """Paginated observation query result using HMAC-signed keyset cursors."""

    items: list[dict[str, Any]]
    next_cursor: Optional[str] = None
    has_more: bool = False
    total_count: Optional[int] = None


@runtime_checkable
class IPerceptionEngine(Protocol):
    """Perception Engine: translates raw inputs into structured observations."""

    async def process(
        self,
        raw_input: Any,
        context: BrainContext,
        task_metadata: Optional[dict[str, Any]] = None,
    ) -> EngineResult:
        ...


@runtime_checkable
class IObservationEngine(Protocol):
    """Observation Engine: persists structured observations and provides cursor pagination."""

    async def record_observation(
        self,
        observation_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        ...

    async def list_observations(
        self,
        context: BrainContext,
        cursor: Optional[str] = None,
        limit: int = 50,
        filters: Optional[dict[str, Any]] = None,
    ) -> ObservationFeedResult:
        ...


@runtime_checkable
class IContextEngine(Protocol):
    """Context Engine: resolves and validates organizational and case boundaries."""

    async def resolve_context(
        self,
        request_scope: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        ...


@runtime_checkable
class IMemoryEngine(Protocol):
    """Memory Engine: manages knowledge candidates and human validation lifecycle."""

    async def store_candidate(
        self,
        fact_data: dict[str, Any],
        context: BrainContext,
    ) -> EngineResult:
        ...

    async def get_record(
        self,
        record_id: UUID,
        context: BrainContext,
    ) -> EngineResult:
        ...

    async def validate_candidate(
        self,
        record_id: UUID,
        action: str,  # "VALIDATE" or "REJECT"
        context: BrainContext,
    ) -> EngineResult:
        ...


@runtime_checkable
class IRetrievalEngine(Protocol):
    """Retrieval Engine: candidate selection, strict case isolation, and ranking."""

    async def search(
        self,
        query: str,
        context: BrainContext,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> EngineResult:
        ...


@runtime_checkable
class IPlanningEngine(Protocol):
    """Planning Engine: declarative plan formulation and evidence-based replanning.
    
    Advisory 6th capability under ADR-008. Has zero execution authority.
    """

    async def create_plan(
        self,
        goal: str,
        context: BrainContext,
        max_replans: int = 2,
    ) -> Any:  # Returns Plan model
        ...

    async def request_replan(
        self,
        plan: Any,
        failure_evidence: dict[str, Any],
        context: BrainContext,
    ) -> Any:  # Returns revised Plan model
        ...
