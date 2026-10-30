"""Legal Structured Knowledge Extractor for Brain-Co Legal Domain.

Extracts Egyptian Civil Law and legal contract structures:
- Document type, title, parties, dates, entities, facts, obligations
- Page provenance retention
- LLM-assisted and deterministic extraction for Egyptian commercial law
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from ai.core.services.llm_service import LLMService
from app.domains.legal.schemas import (
    DocumentStructuredKnowledge,
    DocumentType,
    ExtractedEntity,
    ExtractedFact,
    ExtractedObligation,
    FactCategory,
)
from app.ring1.pdf.schemas import PDFExtractionResult

logger = logging.getLogger("domains.legal.extractor")


class LegalStructuredKnowledgeExtractor:
    """Specialized Legal Domain Extractor for Egyptian Civil Law and commercial contracts."""

    def __init__(self, llm_service: Optional[LLMService] = None) -> None:
        self.llm_service = llm_service

    async def extract(
        self,
        extraction_result: PDFExtractionResult,
    ) -> DocumentStructuredKnowledge:
        """Alias for extract_knowledge."""
        return await self.extract_knowledge(extraction_result)

    async def extract_knowledge(
        self,
        extraction_result: PDFExtractionResult,
    ) -> DocumentStructuredKnowledge:
        """Extract structured legal knowledge from page-by-page text."""
        if extraction_result.is_scanned or extraction_result.total_characters == 0:
            return DocumentStructuredKnowledge(
                document_id=extraction_result.document_id,
                document_type=DocumentType.GENERAL_DOCUMENT,
                title=extraction_result.original_filename,
                summary="Scanned or empty document. OCR processing required for text extraction.",
            )

        if self.llm_service is not None:
            try:
                llm_knowledge = await self._extract_with_llm(extraction_result)
                if llm_knowledge is not None:
                    return llm_knowledge
            except Exception as exc:
                logger.warning("LLM structured legal extraction failed, falling back to deterministic: %s", exc)

        return self._extract_deterministic(extraction_result)

    async def _extract_with_llm(
        self,
        extraction_result: PDFExtractionResult,
    ) -> Optional[DocumentStructuredKnowledge]:
        bounded_pages = extraction_result.pages[:5]
        page_excerpts = []
        for p in bounded_pages:
            snippet = p.text[:1500] if len(p.text) > 1500 else p.text
            page_excerpts.append(f"--- PAGE {p.page_number} ---\n{snippet}")
        document_text = "\n\n".join(page_excerpts)

        system_prompt = (
            "You are an expert legal and corporate document analyzer for the Organizational Brain.\n"
            "Analyze the provided document text and extract structured information with STRICT provenance.\n"
            "Rules:\n"
            "1. Only state facts directly asserted in the text. NEVER invent names, numbers, or dates.\n"
            "2. For every fact, you MUST specify the page_number and an exact source_excerpt from that page.\n"
            "3. Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "document_type": "contract|legal_brief|court_ruling|regulatory_policy|corporate_document|general_document",\n'
            '  "title": "Document Title",\n'
            '  "summary": "Brief 1-2 sentence factual summary",\n'
            '  "parties": ["Party A", "Party B"],\n'
            '  "dates_and_events": [{"date": "YYYY-MM-DD", "event": "description"}],\n'
            '  "entities": [{"name": "string", "entity_type": "person|organization|court|law", "page_number": int}],\n'
            '  "facts": [{"statement": "string", "category": "legal_fact|obligation|deadline|financial|identity|general", "page_number": int, "source_excerpt": "string"}],\n'
            '  "obligations": [{"description": "string", "responsible_party": "string", "deadline": "string", "page_number": int}]\n'
            "}"
        )

        from ai.core.models.llm_request import LLMMessage, LLMRequest

        req = LLMRequest(
            messages=[
                LLMMessage(role="system", content=system_prompt),
                LLMMessage(role="user", content=document_text),
            ],
            temperature=0.1,
            max_tokens=2500,
        )

        resp = await self.llm_service.generate(req)
        content = resp.content.strip()

        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines).strip()

        data = json.loads(content)

        doc_type_raw = data.get("document_type", "general_document").lower()
        try:
            doc_type = DocumentType(doc_type_raw)
        except ValueError:
            doc_type = DocumentType.GENERAL_DOCUMENT

        entities = [
            ExtractedEntity(
                name=e.get("name", ""),
                entity_type=e.get("entity_type", "organization"),
                page_number=max(1, int(e.get("page_number", 1))),
            )
            for e in data.get("entities", [])
            if e.get("name")
        ]

        facts = []
        for f in data.get("facts", []):
            cat_raw = f.get("category", "general").lower()
            try:
                cat = FactCategory(cat_raw)
            except ValueError:
                cat = FactCategory.GENERAL
            facts.append(
                ExtractedFact(
                    statement=f.get("statement", ""),
                    category=cat,
                    page_number=max(1, int(f.get("page_number", 1))),
                    source_excerpt=f.get("source_excerpt", ""),
                    is_validated=False,
                )
            )

        obligations = [
            ExtractedObligation(
                description=o.get("description", ""),
                responsible_party=o.get("responsible_party"),
                deadline=o.get("deadline"),
                page_number=max(1, int(o.get("page_number", 1))),
            )
            for o in data.get("obligations", [])
            if o.get("description")
        ]

        return DocumentStructuredKnowledge(
            document_id=extraction_result.document_id,
            document_type=doc_type,
            title=data.get("title", extraction_result.original_filename),
            summary=data.get("summary", ""),
            parties=data.get("parties", []),
            dates_and_events=data.get("dates_and_events", []),
            entities=entities,
            facts=facts,
            obligations=obligations,
        )

    def _extract_deterministic(
        self,
        extraction_result: PDFExtractionResult,
    ) -> DocumentStructuredKnowledge:
        """Deterministic fallback extractor for Egyptian legal and commercial documents."""
        full_text = extraction_result.combined_text
        doc_type = DocumentType.GENERAL_DOCUMENT
        title = extraction_result.original_filename

        lower_text = full_text.lower()
        if "contract" in lower_text or "عقد" in full_text or "agreement" in lower_text:
            doc_type = DocumentType.CONTRACT
        elif "brief" in lower_text or "مذكرة" in full_text:
            doc_type = DocumentType.LEGAL_BRIEF
        elif "court" in lower_text or "محكمة" in full_text or "حكم" in full_text:
            doc_type = DocumentType.COURT_RULING

        # Extract title from first page
        if extraction_result.pages and extraction_result.pages[0].text:
            first_lines = [l.strip() for l in extraction_result.pages[0].text.split("\n") if l.strip()]
            if first_lines:
                title = first_lines[0][:150]

        facts: list[ExtractedFact] = []
        entities: list[ExtractedEntity] = []
        obligations: list[ExtractedObligation] = []

        # Scan page by page for Egyptian law articles and contract clauses
        for p in extraction_result.pages:
            text = p.text
            # Egyptian law article references: المادة \d+ or Article \d+
            articles = re.findall(r"(?:المادة|Article)\s+(\d+)", text)
            for art in articles:
                entities.append(
                    ExtractedEntity(
                        name=f"Article {art}",
                        entity_type="law",
                        page_number=p.page_number,
                    )
                )

            # Obligations: التزام or shall or agree to
            for match in re.finditer(r"([^.\n]*?(?:shall|agrees to|يلتزم|يتعهد)[^.\n]*)", text, re.IGNORECASE):
                sentence = match.group(1).strip()
                if len(sentence) > 15:
                    obligations.append(
                        ExtractedObligation(
                            description=sentence[:300],
                            page_number=p.page_number,
                        )
                    )

            # Factual sentences
            sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]
            for s in sentences[:3]:
                facts.append(
                    ExtractedFact(
                        statement=s[:250],
                        category=FactCategory.LEGAL_FACT,
                        page_number=p.page_number,
                        source_excerpt=s[:100],
                        is_validated=False,
                    )
                )

        return DocumentStructuredKnowledge(
            document_id=extraction_result.document_id,
            document_type=doc_type,
            title=title,
            summary=f"Extracted {len(facts)} facts and {len(obligations)} obligations from {len(extraction_result.pages)} pages.",
            parties=[],
            dates_and_events=[],
            entities=entities[:20],
            facts=facts[:25],
            obligations=obligations[:15],
        )


# Backward-compatible alias
StructuredKnowledgeExtractor = LegalStructuredKnowledgeExtractor
