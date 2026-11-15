"""Context Resolution Endpoints for Ring 1 General Brain.

Evaluates execution boundaries, resolves ambiguous references, and establishes
immutable ContextRef scopes server-side.
"""

from __future__ import annotations

from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.context import BrainContext, get_brain_context
from app.models.case import Case
from app.ring1.engines.context import ContextEngine
from app.schemas.ring1_api import ContextResolveRequest, ContextResolveResponse
from app.services.case_service import CaseService

router = APIRouter()

# Engine singleton fallback for backward compatibility
_context_engine = ContextEngine()


def get_context_engine(db: Session = Depends(get_db)) -> ContextEngine:
    """Provide a ContextEngine with authoritative production case validator wired to database."""
    # Preserve monkeypatched validator if a test explicitly configured one on _context_engine
    if getattr(_context_engine, "_case_validator", None) is not None:
        return _context_engine

    def production_case_validator(org_id: str, case_id: str, user_id: Any = None) -> bool:
        if not case_id or not str(case_id).strip():
            return False
        norm_case = str(case_id).strip()
        # 1. Look up by UUID
        try:
            case_uuid = uuid.UUID(norm_case)
            c = CaseService.get_case(db, org_id, case_uuid)
            if c is not None:
                return True
        except (ValueError, AttributeError):
            pass
        # 2. Look up by case_number within tenant organization
        c = db.query(Case).filter(
            Case.organization_id == org_id,
            Case.case_number == norm_case,
        ).first()
        return c is not None

    return ContextEngine(case_validator=production_case_validator)


@router.post(
    "/resolve",
    status_code=status.HTTP_200_OK,
    response_model=ContextResolveResponse,
    summary="Resolve and validate execution context boundaries",
)
async def resolve_context(
    payload: ContextResolveRequest,
    context: BrainContext = Depends(get_brain_context),
    engine: ContextEngine = Depends(get_context_engine),
) -> ContextResolveResponse:
    """Resolve context request, identifying ambiguities and scope constraints."""
    request_scope = {
        "domain_id": payload.domain_id or context.domain_id,
        "case_id": payload.case_id or payload.scope_id or context.effective_scope_id,
        "scope_id": payload.scope_id or payload.case_id or context.effective_scope_id,
        "user_id": payload.user_id or context.user_id,
        "hints": payload.hints,
    }

    result = await engine.resolve_context(
        request_scope=request_scope,
        context=context,
    )

    if result.error:
        err_code = result.error.get("code", "")
        err_msg = result.error.get("message", "Context resolution error")
        if "OVERRIDE" in err_code or "DENIED" in err_code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

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
