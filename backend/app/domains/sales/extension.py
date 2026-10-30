"""Sales Domain Extension for Brain-Co.

Implements IDomainExtension for Enterprise Sales and Deal Intelligence.
Demonstrates multi-domain usage of the General Brain without engine modification.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.context import BrainContext
from app.domains.contracts import IDomainExtension
from app.domains.sales.extractor import SalesConversationExtractor
from app.domains.sales.schemas import DealStage, ObjectionCategory, SalesOpportunity
from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus


class SalesDomainExtension(IDomainExtension):
    """Domain Extension for B2B Sales & Customer Intelligence."""

    @property
    def domain_id(self) -> str:
        return "sales"

    @property
    def display_name(self) -> str:
        return "Enterprise Sales & Customer Intelligence"

    @property
    def version(self) -> str:
        return "1.0.0"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register sales domain capabilities into the registry."""
        registry.register(
            "sales.extract_opportunity",
            self.domain_id,
            self.handle_extract_opportunity,
            description="Extract customer requirements, objections, and deal stage from sales conversations.",
        )

    def get_schemas(self) -> dict[str, Any]:
        """Return sales domain schemas and enums."""
        return {
            "deal_stages": [s.value for s in DealStage],
            "objection_categories": [c.value for c in ObjectionCategory],
            "opportunity_model": "SalesOpportunity",
        }

    async def extract_domain_knowledge(
        self,
        raw_content: Any,
        context: BrainContext,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Extract sales opportunities and deal signals from text."""
        extractor = SalesConversationExtractor()
        text = raw_content if isinstance(raw_content, str) else str(raw_content)
        account = (metadata or {}).get("account_name", "Prospective Account")
        opp = extractor.extract(text, account_name=account)
        return opp.model_dump(mode="json")

    async def handle_extract_opportunity(self, request: MeshRequest) -> MeshResponse:
        """Mesh capability handler for sales opportunity extraction."""
        payload = request.payload or {}
        context = BrainContext(
            organization_id=getattr(request.context_ref, "organization_id", "org-default") if request.context_ref else "org-default",
            case_id=getattr(request.context_ref, "case_id", None) if request.context_ref else None,
            domain_id=self.domain_id,
        )
        content = payload.get("content") or payload.get("text") or ""
        extracted = await self.extract_domain_knowledge(content, context, metadata=payload.get("metadata"))
        return MeshResponse(
            task_id=request.task_id,
            plan_version=request.plan_version,
            source_engine=self.domain_id,
            status=ResultStatus.SUCCESS,
            payload=extracted,
        )
