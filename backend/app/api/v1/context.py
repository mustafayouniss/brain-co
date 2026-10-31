"""Context Resolution Endpoints for Ring 1 General Brain.

Evaluates execution boundaries, resolves ambiguous references, and establishes
immutable ContextRef scopes server-side.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.core.context import BrainContext, get_brain_context
from app.ring1.engines.context import ContextEngine
from app.schemas.ring1_api import ContextResolveRequest, ContextResolveResponse

router = APIRouter()

# Engine singleton for context boundary evaluation
_context_engine = ContextEngine()


@router.post(
    "/resolve",
    status_code=status.HTTP_200_OK,
    response_model=ContextResolveResponse,
    summary="Resolve and validate execution context boundaries",
)
async def resolve_context(
    payload: ContextResolveRequest,
    context: BrainContext = Depends(get_brain_context),
) -> ContextResolveResponse:
    """Resolve context request, identifying ambiguities and scope constraints."""
    request_scope = {
        "domain_id": payload.domain_id or context.domain_id,
        "case_id": payload.case_id or payload.scope_id or context.effective_scope_id,
        "scope_id": payload.scope_id or payload.case_id or context.effective_scope_id,
        "user_id": payload.user_id or context.user_id,
        "hints": payload.hints,
    }

    result = await _context_engine.resolve_context(
        request_scope=request_scope,
        context=context,
    )

    data = result.data or {}
    return ContextResolveResponse(
        context_ref_id=data.get("context_ref", "ctx-unresolved"),
        organization_id=context.organization_id,
        domain_id=data.get("domain_id") or payload.domain_id,
        case_id=data.get("case_id"),
        scope_id=data.get("scope_id") or data.get("case_id"),
        user_id=data.get("user_id") or context.user_id,
        resolution_status=data.get("resolution_status", "INSUFFICIENT_DATA"),
        ambiguities=data.get("ambiguities", []),
        scope_constraints=data.get("scope_constraints", []),
    )
