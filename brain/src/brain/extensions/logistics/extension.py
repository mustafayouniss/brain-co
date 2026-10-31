"""Logistics Fleet Domain Extension for Brain-Co (Fictional Domain).

Implements IDomainExtension for Global Maritime Fleet & Cargo Logistics.
Proves complete domain-agnostic capability of the General Brain engines.
"""

from __future__ import annotations

from typing import Any, Optional

from brain.extensions.logistics.extractor import MaritimeManifestExtractor
from brain.extensions.logistics.schemas import VoyageManifest, VoyageStage
from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.context import BrainContext
from brain.general.contracts.domain import IDomainExtension
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus


class LogisticsFleetDomainExtension(IDomainExtension):
    """Domain Extension for Maritime Fleet and Cargo Logistics."""

    @property
    def domain_id(self) -> str:
        return "logistics"

    @property
    def display_name(self) -> str:
        return "Global Maritime Fleet & Logistics"

    @property
    def version(self) -> str:
        return "1.0.0"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register logistics domain capabilities into the registry."""
        registry.register(
            "logistics.parse_manifest",
            self.domain_id,
            self.handle_parse_manifest,
            description="Parse vessel manifest, voyage stages, and hazardous cargo inspections.",
        )

    def get_schemas(self) -> dict[str, Any]:
        """Return logistics domain schemas and enums."""
        return {
            "voyage_stages": [s.value for s in VoyageStage],
            "manifest_model": "VoyageManifest",
            "inspection_model": "CargoInspection",
        }

    async def extract_domain_knowledge(
        self,
        raw_content: Any,
        context: BrainContext,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Extract maritime manifest and cargo inspection data."""
        extractor = MaritimeManifestExtractor()
        text = raw_content if isinstance(raw_content, str) else str(raw_content)
        vessel = (metadata or {}).get("vessel_name", "MV Pioneer Star")
        manifest = extractor.extract(text, vessel_name=vessel)
        return manifest.model_dump(mode="json")

    async def handle_parse_manifest(self, request: MeshRequest) -> MeshResponse:
        """Mesh capability handler for voyage manifest parsing."""
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


__all__ = ["LogisticsFleetDomainExtension"]
