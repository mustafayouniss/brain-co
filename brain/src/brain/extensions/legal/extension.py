"""Legal Domain Extension Module for Brain-Co.

Implements IDomainExtension for Egyptian Civil Law and corporate legal intelligence.
Registers legal capabilities with General Brain CapabilityRegistry.
"""

from __future__ import annotations

import io
from typing import Any, Optional

from brain.extensions.legal.extractor import LegalStructuredKnowledgeExtractor
from brain.extensions.legal.schemas import (
    DocumentStructuredKnowledge,
    DocumentType,
    ExtractedEntity,
    ExtractedFact,
    ExtractedObligation,
    FactCategory,
    PDFExtractionResult,
    PDFPageContent,
)
from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.context import BrainContext
from brain.general.contracts.domain import IDomainExtension
from brain.general.contracts.envelopes import MeshRequest, MeshResponse, ResultStatus


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
            # Parse PDF bytes into PDFExtractionResult
            filename = (metadata or {}).get("filename", "document.pdf")
            try:
                import pypdf
                reader = pypdf.PdfReader(io.BytesIO(raw_content))
                pages = []
                total_chars = 0
                for idx, p in enumerate(reader.pages, start=1):
                    p_text = p.extract_text() or ""
                    total_chars += len(p_text)
                    pages.append(
                        PDFPageContent(
                            page_number=idx,
                            text=p_text,
                            char_count=len(p_text),
                            word_count=len(p_text.split()),
                            is_blank=not bool(p_text.strip()),
                        )
                    )
                extraction_res = PDFExtractionResult(
                    original_filename=filename,
                    file_size_bytes=len(raw_content),
                    checksum_sha256="",
                    page_count=len(pages),
                    total_characters=total_chars,
                    pages=pages,
                    is_scanned=total_chars == 0,
                )
            except Exception:
                extraction_res = PDFExtractionResult(
                    original_filename=filename,
                    file_size_bytes=len(raw_content),
                    checksum_sha256="",
                    page_count=0,
                    total_characters=0,
                    pages=[],
                    is_scanned=True,
                )
            doc_knowledge = await extractor.extract(extraction_res)
            return doc_knowledge.model_dump(mode="json")
        elif isinstance(raw_content, str):
            extraction_res = PDFExtractionResult(
                original_filename=(metadata or {}).get("filename", "text_document.txt"),
                file_size_bytes=len(raw_content.encode("utf-8")),
                checksum_sha256="",
                page_count=1,
                total_characters=len(raw_content),
                pages=[
                    PDFPageContent(
                        page_number=1,
                        text=raw_content,
                        char_count=len(raw_content),
                        word_count=len(raw_content.split()),
                        is_blank=not bool(raw_content.strip()),
                    )
                ],
            )
            doc_knowledge = await extractor.extract(extraction_res)
            return doc_knowledge.model_dump(mode="json")
        return {"error": "Unsupported content format for legal extraction"}

    async def handle_extract_knowledge(self, request: MeshRequest) -> MeshResponse:
        """Capability handler for mesh envelope execution."""
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


__all__ = ["LegalDomainExtension"]
