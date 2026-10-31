"""Compatibility shim for BasicRetrievalEngine.

Adapts legacy constructor signature (db_session_factory) while subclassing
the canonical BasicRetrievalEngine from brain.general.engines.retrieval.
Preserves isinstance checks and exact behavior.
"""

from typing import Optional

from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.storage import IRetrievalStore, IRetrievalStrategy
from brain.general.engines.retrieval import (
    BasicRetrievalEngine as CanonicalBasicRetrievalEngine,
    LexicalRetrievalStrategy,
)
from brain.general.runtime.router import MeshRouter
from brain.general.stores.in_memory_retrieval import InMemoryRetrievalStore


class BasicRetrievalEngine(CanonicalBasicRetrievalEngine):
    """Compatibility adapter for BasicRetrievalEngine accepting legacy db_session_factory."""

    def __init__(
        self,
        db_session_factory=None,
        store: Optional[IRetrievalStore] = None,
        strategy: Optional[IRetrievalStrategy] = None,
        memory_engine=None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        **kwargs,
    ) -> None:
        resolved_store = store
        if resolved_store is None:
            if db_session_factory is not None:
                from app.infrastructure.database.stores import (
                    SqlAlchemyRetrievalStore,
                )

                resolved_store = SqlAlchemyRetrievalStore(db_session_factory)
            else:
                resolved_store = InMemoryRetrievalStore()

        super().__init__(
            store=resolved_store,
            strategy=strategy,
            memory_engine=memory_engine,
            llm_client=llm_client,
            mesh_router=mesh_router,
        )
        self._db_session_factory = db_session_factory


__all__ = [
    "BasicRetrievalEngine",
    "CanonicalBasicRetrievalEngine",
    "LexicalRetrievalStrategy",
]
