"""Storage and Persistence Protocols for General Brain.

Engines depend exclusively on these protocols and have zero direct coupling to
SQLAlchemy, database sessions, or persistence engines.
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from brain.general.contracts.context import BrainContext
from brain.general.contracts.protocols import ObservationFeedResult


@runtime_checkable
class IObservationStore(Protocol):
    """Protocol for observation persistence and feed retrieval."""

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        """Return existing observation payload by idempotency key if found."""
        ...

    async def save(self, observation: dict[str, Any]) -> str:
        """Persist normalized observation and return its unique identifier."""
        ...

    async def list_feed(
        self,
        organization_id: str,
        case_id: Optional[str] = None,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        cursor_created_at: Optional[str] = None,
        cursor_id: Optional[str] = None,
    ) -> ObservationFeedResult:
        """Query observation feed bounded by scope and keyset pagination."""
        ...


@runtime_checkable
class IMemoryStore(Protocol):
    """Protocol for knowledge records and candidate lifecycle persistence."""

    async def find_by_idempotency_key(self, idempotency_key: str) -> Optional[dict[str, Any]]:
        """Return existing memory record by idempotency key if found."""
        ...

    async def save_record(self, record: dict[str, Any]) -> str:
        """Persist memory candidate/record and return its unique identifier."""
        ...

    async def get_record(
        self,
        record_id: str,
        organization_id: str,
        case_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Retrieve an authorized memory record by ID with strict scope boundaries."""
        ...

    async def update_status(
        self,
        record_id: str,
        organization_id: str,
        new_status: str,
        validation_authority: bool,
        metadata: Optional[dict[str, Any]] = None,
    ) -> bool:
        """Update candidate lifecycle status. Requires explicit validation authority."""
        ...


@runtime_checkable
class IRetrievalStore(Protocol):
    """Protocol for searching stored knowledge and observation records."""

    async def search_records(
        self,
        query: str,
        organization_id: str,
        case_id: Optional[str] = None,
        record_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Retrieve records matching query under authorized scope boundaries."""
        ...


@runtime_checkable
class IRetrievalStrategy(Protocol):
    """Search ranking and candidate selection strategy."""

    async def execute_search(
        self,
        query: str,
        context: BrainContext,
        limit: int,
        offset: int,
        filters: Optional[dict[str, Any]],
        store: IRetrievalStore,
    ) -> list[dict[str, Any]]:
        """Execute candidate selection, scope filtering, ranking, and assembly."""
        ...
