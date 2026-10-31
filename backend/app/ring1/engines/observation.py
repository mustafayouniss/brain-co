"""Compatibility shim for ObservationEngine.

Adapts legacy constructor signature (db_session_factory) while subclassing
the canonical ObservationEngine from brain.general.engines.observation.
Preserves isinstance checks and exact behavior.
"""

from typing import Optional

from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.storage import IObservationStore
from brain.general.engines.observation import (
    ObservationEngine as CanonicalObservationEngine,
)
from brain.general.runtime.router import MeshRouter
from brain.general.stores.in_memory_observation import InMemoryObservationStore


class ObservationEngine(CanonicalObservationEngine):
    """Compatibility adapter for ObservationEngine accepting legacy db_session_factory."""

    def __init__(
        self,
        db_session_factory=None,
        store: Optional[IObservationStore] = None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        **kwargs,
    ) -> None:
        resolved_store = store
        if resolved_store is None:
            if db_session_factory is not None:
                from app.infrastructure.database.stores import (
                    SqlAlchemyObservationStore,
                )

                resolved_store = SqlAlchemyObservationStore(db_session_factory)
            else:
                resolved_store = InMemoryObservationStore()

        super().__init__(
            store=resolved_store,
            llm_client=llm_client,
            mesh_router=mesh_router,
        )
        self._db_session_factory = db_session_factory


__all__ = ["CanonicalObservationEngine", "ObservationEngine"]
