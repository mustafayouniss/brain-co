"""Basic Retrieval Engine — contextual query and search over Ring 1 memory and observations.

Deterministic Core:
- Enforce strict case_id isolation (never return records from other cases)
- Query MemoryRecords and Observations filtered by case_id, record_type, and text
- Lexical substring and metadata matching
- Pagination support (limit, offset)
- In-memory fallback for testing and lightweight execution

Intelligence Layer:
- Query intent analysis / keyword expansion when query terms are broad

Must not: cross context boundaries, leak records across cases,
bypass case_id filtering, return hallucinated records.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ring1.contracts.capabilities import RETRIEVAL_QUERY, CapabilityRegistry
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from app.ring1.contracts.errors import EngineErrorCode
from app.ring1.engines.base import BaseEngine
from app.ring1.models.observation import MemoryRecord, Observation


class BasicRetrievalEngine(BaseEngine):
    """Ring 1 Basic Retrieval Engine [GB].

    Executes context-scoped queries over persisted memory records and observations.
    Context isolation is strictly enforced: queries without a valid case_id
    are rejected, and results from foreign cases are never returned.
    """

    def __init__(
        self,
        db_session_factory=None,
        memory_engine=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._db_session_factory = db_session_factory
        self._memory_engine = memory_engine
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

    # -----------------------------------------------------------------
    # In-memory record feeder (for testing)
    # -----------------------------------------------------------------

    def add_in_memory_record(self, record: dict[str, Any]) -> None:
        """Add a record to the in-memory pool (used during tests)."""
        self._in_memory_records.append(record)

    # -----------------------------------------------------------------
    # Capability: retrieval.query
    # -----------------------------------------------------------------

    async def handle_query(self, request: MeshRequest) -> MeshResponse:
        """Query memory records with strict context isolation.

        Payload expected:
        - query: str (optional search term)
        - record_type: str (optional filter)
        - case_id: str (optional, defaults to request.context_ref.case_id)
        - limit: int (optional, default 10, max 100)
        - offset: int (optional, default 0)
        """
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        # Context boundary check: query MUST have a context_ref or explicit case_id
        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        case_id = request.payload.get("case_id") or (
            context_ref.case_id if context_ref else None
        )

        if not case_id:
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A resolved case_id is required for retrieval to enforce data isolation.",
            )

        query_text = (request.payload.get("query") or "").strip()
        record_type = request.payload.get("record_type")
        limit = min(int(request.payload.get("limit", 10)), 100)
        offset = max(int(request.payload.get("offset", 0)), 0)

        # Intelligence Layer: query keyword extraction if query is complex
        keywords = [query_text.lower()] if query_text else []
        if len(query_text.split()) > 5:
            expanded = await self._extract_keywords(query_text)
            if expanded:
                keywords.extend(expanded)

        if self._db_session_factory is not None:
            return await self._query_db(
                request=request,
                case_id=case_id,
                keywords=keywords,
                record_type=record_type,
                limit=limit,
                offset=offset,
            )
        else:
            return self._query_in_memory(
                request=request,
                case_id=case_id,
                keywords=keywords,
                record_type=record_type,
                limit=limit,
                offset=offset,
            )

    # -----------------------------------------------------------------
    # Database query
    # -----------------------------------------------------------------

    async def _query_db(
        self,
        request: MeshRequest,
        case_id: str,
        keywords: list[str],
        record_type: Optional[str],
        limit: int,
        offset: int,
    ) -> MeshResponse:
        session: Session = self._db_session_factory()
        try:
            # Strictly filter by case_id
            stmt = select(MemoryRecord).where(MemoryRecord.case_id == case_id)

            if record_type:
                stmt = stmt.where(MemoryRecord.record_type == record_type)

            stmt = stmt.order_by(MemoryRecord.created_at.desc())
            all_records = session.execute(stmt).scalars().all()

            results = []
            for rec in all_records:
                # Strictly reject any record from another case (defense in depth)
                if rec.case_id != case_id:
                    continue

                if keywords and any(k for k in keywords if k):
                    rec_payload_str = json.dumps(rec.payload or {}).lower()
                    rec_meta_str = json.dumps(rec.metadata_ or {}).lower()
                    rec_type_str = str(rec.record_type or "").lower()
                    if not any(k in rec_payload_str or k in rec_meta_str or k in rec_type_str for k in keywords if k):
                        continue


                results.append({
                    "record_id": str(rec.id),
                    "record_type": rec.record_type,
                    "case_id": rec.case_id,
                    "context_ref": rec.context_ref,
                    "payload": rec.payload,
                    "metadata": rec.metadata_,
                    "created_at": rec.created_at.isoformat(),
                })

            total_count = len(results)
            paginated = results[offset : offset + limit]

            return self._success(
                request,
                {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "case_id": case_id,
                    "records": paginated,
                },
                context_ref=request.context_ref.ref if request.context_ref else None,
            )
        except Exception as exc:
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.INTERNAL_EXECUTION_ERROR,
                f"Failed to execute retrieval query: {str(exc)}",
            )
        finally:
            session.close()

    # -----------------------------------------------------------------
    # In-memory query
    # -----------------------------------------------------------------

    def _query_in_memory(
        self,
        request: MeshRequest,
        case_id: str,
        keywords: list[str],
        record_type: Optional[str],
        limit: int,
        offset: int,
    ) -> MeshResponse:
        # Collect candidates from internal pool and optionally memory_engine
        candidates: list[dict[str, Any]] = list(self._in_memory_records)
        if self._memory_engine is not None and hasattr(self._memory_engine, "_in_memory_records"):
            candidates.extend(self._memory_engine._in_memory_records.values())

        matched = []
        for rec in candidates:
            # Strict case isolation
            if rec.get("case_id") != case_id:
                continue

            if record_type and rec.get("record_type") != record_type:
                continue

            if keywords and any(k for k in keywords if k):
                payload_str = json.dumps(rec.get("payload") or {}).lower()
                meta_str = json.dumps(rec.get("metadata") or {}).lower()
                rec_type_str = str(rec.get("record_type") or "").lower()
                if not any(k in payload_str or k in meta_str or k in rec_type_str for k in keywords if k):
                    continue

            matched.append(rec)


        total_count = len(matched)
        paginated = matched[offset : offset + limit]

        return self._success(
            request,
            {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "case_id": case_id,
                "records": paginated,
            },
            context_ref=request.context_ref.ref if request.context_ref else None,
        )

    # -----------------------------------------------------------------
    # Intelligence Layer: keyword expansion
    # -----------------------------------------------------------------

    async def _extract_keywords(self, query: str) -> list[str]:
        """Extract search terms using LLM if available."""
        if not self._llm_service:
            # Deterministic fallback: simple token split
            return [w.lower() for w in query.split() if len(w) > 3]

        prompt = (
            "Extract 2-4 key search keywords or synonyms from this user query. "
            "Return JSON array of lowercase strings only, e.g. [\"contract\", \"breach\"]"
        )
        result = await self._call_llm_json(prompt, query)
        if isinstance(result, list):
            return [str(k).lower() for k in result if isinstance(k, str)]
        return [w.lower() for w in query.split() if len(w) > 3]
