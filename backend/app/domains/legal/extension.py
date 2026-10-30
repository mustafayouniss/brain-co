"""Legal Domain Extension Module for Brain-Co.

Implements IDomainExtension for Egyptian Civil Law and corporate legal intelligence.
Registers legal capabilities with General Brain CapabilityRegistry.
"""

from __future__ import annotations

from typing import Any, Optional

from app.core.context import BrainContext
from app.domains.contracts import IDomainExtension
from app.domains.legal.extractor import LegalStructuredKnowledgeExtractor
from app.domains.legal.schemas import DocumentStructuredKnowledge, DocumentType, FactCategory
from app.ring1.contracts.capabilities import CapabilityRegistry
from app.ring1.contracts.envelopes import MeshRequest, MeshResponse
from app.ring1.pdf.extractor import PDFExtractor, PDFExtractionResult


class LegalDomainExtension(IDomainExtension):
    """Domain Extension for Legal Intelligence (Egyptian Civil Law)."""

    @property
    def domain_id(self) -> str:
        return "legal"

    @property
    def display_name(self) -> str:
        return "Legal Intelligence (Egyptian Civil Law)"

    @property
    def version(self) -> str:
        return "1.0.0"

    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register legal domain capabilities into the registry."""
        registry.register(
            "legal.extract_knowledge",
            self.domain_id,
            self.handle_extract_knowledge,
            description="Extract structured legal facts, entities, and obligations from document text.",
        )

    def get_schemas(self) -> dict[str, Any]:
        """Return legal domain schemas and enums."""
        return {
            "document_types": [d.value for d in DocumentType],
            "fact_categories": [f.value for f in FactCategory],
            "knowledge_model": "DocumentStructuredKnowledge",
        }

    async def extract_domain_knowledge(
        self,
        raw_content: Any,
        context: BrainContext,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Extract legal domain knowledge from raw content or PDF bytes."""
        extractor = LegalStructuredKnowledgeExtractor()
        if isinstance(raw_content, bytes):
            pdf_extractor = PDFExtractor()
            filename = (metadata or {}).get("filename", "document.pdf")
            extraction_res = pdf_extractor.extract(raw_content, filename=filename)
            doc_knowledge = await extractor.extract(extraction_res)
            return doc_knowledge.model_dump(mode="json")
        elif isinstance(raw_content, str):
            # Text based extraction
            extraction_res = PDFExtractionResult(
                original_filename=(metadata or {}).get("filename", "text_document.txt"),
                file_size_bytes=len(raw_content.encode("utf-8")),
                checksum_sha256="",
                page_count=1,
                total_characters=len(raw_content),
                pages=[],
            )
            # Simple text parsing fallback
            return {
                "document_type": DocumentType.GENERAL_DOCUMENT.value,
                "title": (metadata or {}).get("filename", "text_document.txt"),
                "summary": raw_content[:200],
                "facts": [],
                "entities": [],
                "obligations": [],
            }
        return {"error": "Unsupported content format for legal extraction"}

    async def handle_extract_knowledge(self, request: MeshRequest) -> MeshResponse:
        """Capability handler for mesh envelope execution."""
        from app.ring1.contracts.envelopes import ResultStatus
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
