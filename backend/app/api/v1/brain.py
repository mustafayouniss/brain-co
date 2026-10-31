"""General Brain Status Endpoint.

Provides health, active cognitive engines, registered capabilities,
and registered domain extensions.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings
from app.domains.contracts import domain_registry
from app.ring1.contracts.capabilities import ALL_CAPABILITIES
from app.schemas.ring1_api import BrainStatusResponse

router = APIRouter()


@router.get(
    "/status",
    response_model=BrainStatusResponse,
    summary="General Brain health and registered capabilities",
)
def get_brain_status(db: Session = Depends(get_db)) -> BrainStatusResponse:
    """Return General Brain engine status, capabilities, and active domains."""
    # Check DB health
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    domains = domain_registry.list_domains()
    if "legal" not in domains:
        domains.append("legal")
    domains = sorted(list(set(domains)))

    return BrainStatusResponse(
        status="online" if db_ok else "degraded",
        engines=[
            "perception",
            "observation",
            "context",
            "memory",
            "retrieval",
            "planning",
        ],
        planning_advisory=True,
        registered_capabilities=sorted(list(ALL_CAPABILITIES)),
        registered_domains=domains,
        organization_id=getattr(settings, "ORGANIZATION_ID", "org-brain-corp"),
        environment=settings.ENVIRONMENT,
    )
