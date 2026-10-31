"""Compatibility shim for BasicMemoryEngine.

Adapts legacy constructor signature (db_session_factory) while subclassing
the canonical BasicMemoryEngine from brain.general.engines.memory.
Preserves isinstance checks and exact behavior.
"""

from typing import Optional

from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.storage import IMemoryStore
from brain.general.engines.memory import (
    BasicMemoryEngine as CanonicalBasicMemoryEngine,
)
from brain.general.runtime.router import MeshRouter
from brain.general.stores.in_memory_memory import InMemoryMemoryStore


class BasicMemoryEngine(CanonicalBasicMemoryEngine):
    """Compatibility adapter for BasicMemoryEngine accepting legacy db_session_factory."""

    def __init__(
        self,
        db_session_factory=None,
        store: Optional[IMemoryStore] = None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        **kwargs,
    ) -> None:
        resolved_store = store
        if resolved_store is None:
            if db_session_factory is not None:
                from app.infrastructure.database.stores import SqlAlchemyMemoryStore

                resolved_store = SqlAlchemyMemoryStore(db_session_factory)
            else:
                resolved_store = InMemoryMemoryStore()

        super().__init__(
            store=resolved_store,
            llm_client=llm_client,
            mesh_router=mesh_router,
        )
        self._db_session_factory = db_session_factory


__all__ = ["BasicMemoryEngine", "CanonicalBasicMemoryEngine"]
