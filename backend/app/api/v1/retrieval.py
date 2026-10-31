"""Context-First Lexical Retrieval Endpoints for Ring 1 General Brain.

Enforces strict tenant isolation and scope isolation BEFORE candidate ranking.
Excludes unvalidated knowledge candidates from ordinary trusted retrieval.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context import BrainContext, get_brain_context
from app.ring1.models.observation import MemoryRecord
from app.schemas.ring1_api import RetrievalItem, RetrievalSearchResponse

router = APIRouter()


@router.get(
    "/search",
    response_model=RetrievalSearchResponse,
    summary="Context-first lexical search over authorized memory records",
)
def search_records(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=100, description="Max results to return"),
    record_type: Optional[str] = Query(None, description="Optional record_type filter"),
    include_candidates: bool = Query(
        False, description="Include unvalidated candidate knowledge (requires validation authority)"
    ),
    db: Session = Depends(get_db),
    context: BrainContext = Depends(get_brain_context),
) -> RetrievalSearchResponse:
    """Execute context-first keyword retrieval strictly bounded by organization and scope."""
    # 1. Base query strictly filtered by organization
    query = db.query(MemoryRecord).filter(
        MemoryRecord.organization_id == context.organization_id
    )

    # 2. Scope boundary enforcement
    if context.effective_scope_id:
        query = query.filter(MemoryRecord.case_id == context.effective_scope_id)

    # 3. Optional record type filter
    if record_type:
        query = query.filter(MemoryRecord.record_type == record_type)

    # 4. Candidate filtering: candidates excluded unless caller has validation authority
    if not (include_candidates and context.validation_authority):
        query = query.filter(MemoryRecord.status.notin_(["candidate", "rejected"]))

    candidates = query.all()

    # 5. Lexical keyword scoring and filtering
    query_terms = [t.lower().strip() for t in q.split() if t.strip()]
    if not query_terms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_QUERY", "message": "Search query contains no search terms"},
        )

    scored_items: list[RetrievalItem] = []
    for rec in candidates:
        payload_str = json.dumps(rec.payload or {}, default=str).lower()
        score = 0.0
        matching_snippets: list[str] = []

        for term in query_terms:
            count = payload_str.count(term)
            if count > 0:
                score += count * 1.0
                idx = payload_str.find(term)
                start = max(0, idx - 40)
                end = min(len(payload_str), idx + 80)
                snippet = payload_str[start:end].replace('"', " ").strip()
                matching_snippets.append(f"...{snippet}...")

        if score > 0.0:
            best_snippet = matching_snippets[0] if matching_snippets else f"Record {rec.id}"
            scored_items.append(
                RetrievalItem(
                    record_id=str(rec.id),
                    record_type=rec.record_type,
                    case_id=rec.case_id,
                    status=rec.status,
                    score=round(score, 2),
                    snippet=best_snippet,
                    payload=rec.payload or {},
                )
            )

    # Sort descending by score
    scored_items.sort(key=lambda x: x.score, reverse=True)
    results = scored_items[:limit]

    return RetrievalSearchResponse(
        query=q,
        items=results,
        total_found=len(scored_items),
        organization_id=context.organization_id,
        case_id=context.effective_scope_id,
        scope_id=context.effective_scope_id,
    )
