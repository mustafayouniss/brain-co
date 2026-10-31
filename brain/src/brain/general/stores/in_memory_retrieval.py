"""In-memory retrieval store and lexical retrieval strategy for General Brain.

Provides candidate selection, strict scope filtering, and token-based lexical ranking
without requiring database sessions or pgvector.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Optional

from brain.general.contracts.context import BrainContext
from brain.general.contracts.storage import IRetrievalStore, IRetrievalStrategy


class InMemoryRetrievalStore(IRetrievalStore):
    """Thread-safe in-memory retrieval store over memory and observation records."""

    def __init__(
        self,
        records: Optional[list[dict[str, Any]]] = None,
        memory_store: Optional[Any] = None,
    ) -> None:
        self._lock = threading.RLock()
        self._memory_store = memory_store
        if isinstance(records, list):
            self._records = list(records)
        elif records is not None and hasattr(records, "list_all"):
            self._records = []
            self._memory_store = records
        else:
            self._records = []

    def add_records(self, new_records: list[dict[str, Any]]) -> None:
        with self._lock:
            existing_ids = {r.get("record_id") or r.get("id") for r in self._records if r.get("record_id") or r.get("id")}
            for r in new_records:
                rid = r.get("record_id") or r.get("id")
                if not rid or rid not in existing_ids:
                    self._records.append(r)
                    if rid:
                        existing_ids.add(rid)

    async def search_records(
        self,
        query: str,
        organization_id: str,
        case_id: Optional[str] = None,
        record_type: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with self._lock:
            pool = list(self._records)
            if self._memory_store is not None and hasattr(self._memory_store, "list_all"):
                existing_ids = {r.get("record_id") or r.get("id") for r in pool if r.get("record_id") or r.get("id")}
                for mr in self._memory_store.list_all():
                    m_id = mr.get("record_id") or mr.get("id")
                    if not m_id or m_id not in existing_ids:
                        pool.append(mr)

            results = []
            tokens = [t.lower() for t in re.findall(r"\w+", query)] if query else []

            for rec in pool:
                # 1. Organization isolation
                if rec.get("organization_id") and rec.get("organization_id") != organization_id:
                    continue

                # 2. Case isolation
                rec_case = rec.get("case_id") or rec.get("scope_id")
                if case_id and rec_case != case_id:
                    continue

                # 3. Filter rejected records
                if rec.get("status") == "rejected":
                    continue

                # 4. Optional record_type filter
                if record_type and rec.get("record_type") != record_type:
                    continue

                # 5. Score matching
                rec_type_str = str(rec.get("record_type") or "").lower()
                payload_str = str(rec.get("payload") or "").lower()
                meta_str = str(rec.get("metadata") or "").lower()
                content = f"{rec_type_str} {payload_str} {meta_str} {str(rec.get('content') or '').lower()}"
                score = 0
                for token in tokens:
                    if token in content:
                        score += 1

                if not tokens or score > 0:
                    scored_rec = dict(rec)
                    scored_rec["_score"] = score
                    results.append(scored_rec)

            results.sort(key=lambda x: x.get("_score", 0), reverse=True)
            for r in results:
                r.pop("_score", None)

            return results[offset : offset + limit]


class LexicalRetrievalStrategy(IRetrievalStrategy):
    """Deterministic lexical retrieval strategy.
    
    Performs candidate selection, strict case isolation, term-frequency
    ranking, and result assembly without claiming semantic vector retrieval.
    """

    async def execute_search(
        self,
        query: str,
        context: BrainContext,
        limit: int,
        offset: int,
        filters: Optional[dict[str, Any]],
        store: IRetrievalStore,
    ) -> list[dict[str, Any]]:
        record_type = filters.get("record_type") if filters else None
        return await store.search_records(
            query=query,
            organization_id=context.organization_id,
            case_id=context.effective_scope_id,
            record_type=record_type,
            limit=limit,
            offset=offset,
        )
