"""Basic Retrieval Engine — contextual query and search over General Brain records.

Deterministic Core:
- Enforce strict case_id and organization_id isolation (never return records from other cases)
- Strategy boundary separating search strategy from storage
- Step-by-step pipeline: candidate selection -> scope filtering -> ranking -> result assembly
- Lexical keyword and metadata token ranking (non-vector baseline)
- Pagination support (limit, offset)

Intelligence Layer:
- Query intent analysis / keyword expansion when query terms are broad

Must not: cross context boundaries, leak records across cases,
bypass case_id filtering, pretend ILIKE is semantic search, create unapproved vector schemas,
or depend directly on database infrastructure.
"""

from __future__ import annotations

from typing import Any, Optional

from brain.general.contracts.capabilities import RETRIEVAL_QUERY, CapabilityRegistry
from brain.general.contracts.context import BrainContext
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus
from brain.general.contracts.errors import EngineErrorCode, StorageConfigurationError
from brain.general.contracts.llm import ILLMClient
from brain.general.contracts.protocols import EngineResult, IMemoryEngine, IRetrievalEngine
from brain.general.contracts.storage import IRetrievalStore, IRetrievalStrategy
from brain.general.engines.base import BaseEngine
from brain.general.runtime.router import MeshRouter
from brain.general.stores.in_memory_retrieval import LexicalRetrievalStrategy


class BasicRetrievalEngine(BaseEngine, IRetrievalEngine):
    """General Brain Basic Retrieval Engine [GB].

    Context-first retrieval engine with strategy separation. Requires an explicit
    IRetrievalStore implementation injected at initialization.
    """

    def __init__(
        self,
        store: Optional[IRetrievalStore] = None,
        strategy: Optional[IRetrievalStrategy] = None,
        memory_engine: Optional[IMemoryEngine] = None,
        llm_client: Optional[ILLMClient] = None,
        mesh_router: Optional[MeshRouter] = None,
        llm_service: Optional[ILLMClient] = None,
        **kwargs: Any,
    ) -> None:
        if store is None:
            raise StorageConfigurationError(
                "BasicRetrievalEngine requires an explicit IRetrievalStore implementation. "
                "For test or CLI use, inject InMemoryRetrievalStore(). "
                "For production, inject a database store adapter."
            )
        super().__init__(
            llm_client=llm_client,
            mesh_router=mesh_router,
            llm_service=llm_service,
            **kwargs,
        )
        self._store = store
        self._strategy = strategy or LexicalRetrievalStrategy()
        self._memory_engine = memory_engine

    @property
    def store(self) -> IRetrievalStore:
        return self._store

    @property
    def engine_name(self) -> str:
        return "retrieval"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        registry.register(
            RETRIEVAL_QUERY,
            self.engine_name,
            self.handle_query,
            description="Query stored records with contextual scoping and ranking.",
        )

    def add_in_memory_record(self, record: dict[str, Any]) -> None:
        """Add record directly to in-memory store (used in tests)."""
        if hasattr(self._store, "add_records"):
            self._store.add_records([record])
        elif hasattr(self._store, "_records"):
            self._store._records.append(record)

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
        """Transport-independent contextual search."""
        if not context or not context.organization_id:
            return EngineResult(
                error={"code": "INVALID_CONTEXT", "message": "Valid BrainContext with organization_id required"}
            )
        if not context.case_id or not str(context.case_id).strip():
            return EngineResult(
                error={"code": "CONTEXT_MISSING", "message": "Non-empty case_id required for retrieval"}
            )

        q = (query or "").strip()
        f = filters or {}
        offset = int(f.get("offset", 0))

        # Query expansion via Intelligence Layer if enabled
        expanded_query = q
        if q and self._llm_client and f.get("semantic_expansion", False):
            expanded = await self._expand_query(q)
            if expanded:
                expanded_query = expanded

        # Collect in-memory records from attached memory engine if present
        if self._memory_engine is not None and hasattr(self._store, "add_records"):
            mem_records = []
            if hasattr(self._memory_engine, "_in_memory_records"):
                mem_records = list(self._memory_engine._in_memory_records.values())
            elif hasattr(self._memory_engine, "store") and hasattr(self._memory_engine.store, "records"):
                mem_records = list(self._memory_engine.store.records.values())
            if mem_records:
                self._store.add_records(mem_records)

        results = await self._strategy.execute_search(
            query=expanded_query,
            context=context,
            limit=limit,
            offset=offset,
            filters=f,
            store=self._store,
        )

        data = {
            "query": q,
            "case_id": context.effective_scope_id,
            "total_results": len(results),
            "results": results,
            "records": results,
            "count": len(results),
            "limit": limit,
            "offset": offset,
            "has_more": len(results) >= limit,
            "scope_enforced": {
                "organization_id": context.organization_id,
                "case_id": context.effective_scope_id,
            },
        }
        return EngineResult(data=data, is_terminal=True)

    # -----------------------------------------------------------------
    # Capability handler (Mesh Adapter for Backward Compatibility)
    # -----------------------------------------------------------------

    async def handle_query(self, request: MeshRequest) -> MeshResponse:
        """Handle capability: retrieval.query, enforcing strict context boundaries."""
        validation_err = self.validate_request(request)
        if validation_err:
            return validation_err

        context_err = self.require_context_ref(request)
        if context_err:
            return context_err

        context_ref = request.context_ref
        if not context_ref or not (getattr(context_ref, "case_id", None) or "").strip():
            return self._error(
                request,
                ResultStatus.NEEDS_CLARIFICATION,
                EngineErrorCode.CONTEXT_MISSING,
                "A valid context_ref with non-empty case_id is required for retrieval to enforce data isolation.",
            )

        if not (getattr(context_ref, "organization_id", None) or "").strip():
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

        payload = request.payload
        query_text = (payload.get("query") or "").strip()
        record_type = payload.get("record_type")
        limit = min(int(payload.get("limit") or payload.get("top_k") or 10), 100)
        offset = max(int(payload.get("offset") or 0), 0)
        filters = dict(payload.get("filters", {}))
        if record_type:
            filters["record_type"] = record_type

        context = BrainContext(
            organization_id=authorized_org_id,
            case_id=authorized_case_id,
            user_id=getattr(context_ref, "user_id", None) or getattr(request, "actor_ref", None),
        )

        search_res = await self.search(
            query=query_text,
            context=context,
            limit=limit,
            filters={**filters, "offset": offset},
        )

        if search_res.error:
            code = search_res.error.get("code")
            msg = search_res.error.get("message", "Retrieval failed")
            if code == "CONTEXT_MISSING":
                return self._error(
                    request,
                    ResultStatus.NEEDS_CLARIFICATION,
                    EngineErrorCode.CONTEXT_MISSING,
                    msg,
                )
            return self._error(
                request,
                ResultStatus.FAILED,
                EngineErrorCode.INTERNAL_ERROR,
                msg,
            )

        results = search_res.data.get("results", [])
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
            context_ref=getattr(context_ref, "ref", str(context_ref)),
        )

    # -----------------------------------------------------------------
    # Intelligence Layer: Query expansion
    # -----------------------------------------------------------------

    async def _expand_query(self, query: str) -> Optional[str]:
        """Expand broad queries using Intelligence Layer."""
        if not self._llm_client:
            return None

        prompt = (
            "You are the Retrieval Engine of Ring 1 General Brain. "
            "Given this search query, provide 3 to 5 relevant synonyms or related keywords "
            "to improve search recall. Return JSON: {'expanded_terms': [str]}."
        )
        res = await self._call_llm_json(prompt, f"query: {query}")
        if res and isinstance(res, dict) and "expanded_terms" in res:
            terms = res["expanded_terms"]
            if isinstance(terms, list):
                return f"{query} {' '.join(str(t) for t in terms)}"
        return None


__all__ = ["BasicRetrievalEngine", "LexicalRetrievalStrategy"]
