"""Basic Retrieval Engine — contextual query and search over Ring 1 memory and observations.

Deterministic Core:
- Enforce strict case_id and organization_id isolation (never return records from other cases)
- Strategy boundary separating search strategy from storage
- Step-by-step pipeline: candidate selection -> scope filtering -> ranking -> result assembly
- Lexical keyword and metadata token ranking (non-vector baseline)
- Extensible architecture ready for future vector retrieval once model/dimensions approved
- Pagination support (limit, offset)
- In-memory fallback for testing and lightweight execution

Intelligence Layer:
- Query intent analysis / keyword expansion when query terms are broad

Must not: cross context boundaries, leak records across cases,
bypass case_id filtering, pretend ILIKE is semantic search, create unapproved vector schemas.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import re
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.context import BrainContext
from app.ring1.contracts.capabilities import RETRIEVAL_QUERY, CapabilityRegistry
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.contracts.protocols import EngineResult, IRetrievalEngine
from app.ring1.engines.base import BaseEngine
from app.ring1.models.observation import MemoryRecord, Observation


class IRetrievalStrategy(ABC):
    """Abstract retrieval strategy separating search ranking from persistence."""

    @abstractmethod
    async def execute_search(
        self,
        query: str,
        context: BrainContext,
        limit: int,
        offset: int,
        filters: Optional[dict[str, Any]],
        db_session_factory: Any,
        in_memory_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Execute candidate selection, scope filtering, ranking, and assembly."""
        ...


class LexicalRetrievalStrategy(IRetrievalStrategy):
    """Deterministic lexical retrieval strategy.
    
    Performs explicit candidate selection, strict case isolation, term-frequency
    ranking, and result assembly without claiming semantic vector retrieval.
    """

    async def execute_search(
        self,
        query: str,
        context: BrainContext,
        limit: int,
        offset: int,
        filters: Optional[dict[str, Any]],
        db_session_factory: Any,
        in_memory_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        # 1. Scope Filtering & Candidate Selection
        raw_candidates = await self._fetch_scoped_candidates(
            context=context,
            filters=filters,
            db_session_factory=db_session_factory,
            in_memory_records=in_memory_records,
        )

        # 2. Strict Scope Validation (Defense in Depth)
        scoped_candidates = [
            c for c in raw_candidates
            if c.get("case_id") == context.case_id
            and (not c.get("organization_id") or c.get("organization_id") == context.organization_id)
        ]

        # 3. Candidate Scoring and Ranking
        query_tokens = [t.lower() for t in re.findall(r"\w+", query)] if query else []
        ranked_candidates = []

        for c in scoped_candidates:
            score = self._compute_relevance_score(c, query_tokens)
            if query_tokens and score <= 0.0:
                continue  # Filter out non-matching candidates if query provided
            ranked_candidates.append((score, c))

        # Sort by relevance score descending, then recency
        ranked_candidates.sort(key=lambda x: (x[0], x[1].get("created_at", "")), reverse=True)

        # 4. Result Assembly & Keyset/Offset Slicing
        sliced = ranked_candidates[offset : offset + limit]
        assembled = []
        for score, cand in sliced:
            item = dict(cand)
            item["relevance_score"] = round(score, 4)
            assembled.append(item)

        return assembled

    async def _fetch_scoped_candidates(
        self,
        context: BrainContext,
        filters: Optional[dict[str, Any]],
        db_session_factory: Any,
        in_memory_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        record_type = (filters or {}).get("record_type")
        candidates = []

        if db_session_factory is not None:
            session: Session = db_session_factory()
            try:
                stmt = select(MemoryRecord).where(MemoryRecord.case_id == context.case_id)
                if context.organization_id:
                    stmt = stmt.where(
                        (MemoryRecord.organization_id == context.organization_id)
                        | (MemoryRecord.organization_id.is_(None))
                    )
                if record_type:
                    stmt = stmt.where(MemoryRecord.record_type == record_type)

                records = session.execute(stmt).scalars().all()
                for rec in records:
                    candidates.append({
                        "record_id": str(rec.id),
                        "record_type": rec.record_type,
                        "case_id": rec.case_id,
                        "organization_id": rec.organization_id,
                        "context_ref": rec.context_ref,
                        "payload": rec.payload,
                        "metadata": rec.metadata_,
                        "created_at": rec.created_at.isoformat() if rec.created_at else "",
                    })
            finally:
                session.close()
        else:
            for rec in in_memory_records:
                if rec.get("case_id") == context.case_id:
                    if record_type and rec.get("record_type") != record_type:
                        continue
                    candidates.append(rec)

        return candidates

    def _compute_relevance_score(self, candidate: dict[str, Any], query_tokens: list[str]) -> float:
        if not query_tokens:
            return 1.0  # Base match when no search query specified

        payload_str = json.dumps(candidate.get("payload") or {}).lower()
        meta_str = json.dumps(candidate.get("metadata") or {}).lower()
        rec_type_str = str(candidate.get("record_type") or "").lower()
        combined_text = f"{rec_type_str} {payload_str} {meta_str}"

        matches = sum(1 for token in query_tokens if token in combined_text)
        return float(matches) / float(len(query_tokens))


class BasicRetrievalEngine(BaseEngine, IRetrievalEngine):
    """Ring 1 Basic Retrieval Engine [GB].

    Executes context-scoped queries over persisted memory records and observations.
    Delegates candidate selection and ranking to an injectable IRetrievalStrategy.
    """

    def __init__(
        self,
        db_session_factory=None,
        memory_engine=None,
        strategy: Optional[IRetrievalStrategy] = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._db_session_factory = db_session_factory
        self._memory_engine = memory_engine
        self._strategy = strategy or LexicalRetrievalStrategy()
        self._in_memory_records: list[dict[str, Any]] = []

    @property
    def engine_name(self) -> str:
        return "retrieval"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            RETRIEVAL_QUERY,
            self.engine_name,
            self.handle_query,
            description="Query context-scoped records and observations with strict case isolation.",
        )

    def add_in_memory_record(self, record: dict[str, Any]) -> None:
        """Add a record to the in-memory pool (used during tests)."""
        self._in_memory_records.append(record)

    # -----------------------------------------------------------------
    # Pure Engine Protocol implementation (Decoupled from Transport)
    # -----------------------------------------------------------------

    async def search(
        self,
        query: str,
        context: BrainContext,
        limit: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> EngineResult:
        """Execute a context-scoped retrieval query adhering to IRetrievalEngine."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )
        if not context.case_id or not str(context.case_id).strip():
            return EngineResult(
                error={"code": "CONTEXT_MISSING", "message": "Non-empty case_id required for retrieval"}
            )

        clamped_limit = min(max(limit, 1), 100)
        results = await self._strategy.execute_search(
            query=query,
            context=context,
            limit=clamped_limit,
            offset=0,
            filters=filters,
            db_session_factory=self._db_session_factory,
            in_memory_records=self._in_memory_records,
        )

        return EngineResult(
            data={
                "query": query,
                "case_id": context.case_id,
                "total_results": len(results),
                "results": results,
                "records": results,
            },
            is_terminal=True,
        )

    # -----------------------------------------------------------------
    # Capability: retrieval.query (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_query(self, request: MeshRequest) -> MeshResponse:
        """Query memory records with strict context isolation via mesh adapter."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (context_ref.case_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for retrieval to enforce data isolation.",
            )

        if not (context_ref.organization_id or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty organization_id is required for retrieval to enforce data isolation.",
            )

        authorized_case_id = context_ref.case_id.strip()
        authorized_org_id = context_ref.organization_id.strip()

        payload_case_id = request.payload.get("case_id")
        if payload_case_id and str(payload_case_id).strip() != authorized_case_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload case_id does not match authorized context.",
            )

        payload_org_id = request.payload.get("organization_id")
        if payload_org_id and str(payload_org_id).strip() != authorized_org_id:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.AUTHORIZATION_DENIED,
                "Access denied: payload organization_id does not match authorized context.",
            )

        query_text = (request.payload.get("query") or "").strip()
        record_type = request.payload.get("record_type")
        limit = min(int(request.payload.get("limit", 10)), 100)
        offset = max(int(request.payload.get("offset", 0)), 0)

        context = BrainContext(
            organization_id=authorized_org_id,
            case_id=authorized_case_id,
            user_id=getattr(request, "actor_ref", None),
        )

        in_memory = list(self._in_memory_records)
        if self._memory_engine is not None and hasattr(self._memory_engine, "_in_memory_records"):
            in_memory.extend(self._memory_engine._in_memory_records.values())

        filters = {"record_type": record_type} if record_type else None
        results = await self._strategy.execute_search(
            query=query_text,
            context=context,
            limit=limit,
            offset=offset,
            filters=filters,
            db_session_factory=self._db_session_factory,
            in_memory_records=in_memory,
        )

        return self._success(
            request,
            {
                "query": query_text,
                "case_id": authorized_case_id,
                "organization_id": authorized_org_id,
                "total_results": len(results),
                "results": results,
                "records": results,
                "limit": limit,
                "offset": offset,
            },
            context_ref=context_ref.ref if hasattr(context_ref, "ref") else str(context_ref),
        )
