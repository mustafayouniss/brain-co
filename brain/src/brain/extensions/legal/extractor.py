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

from brain.extensions.legal.schemas import (
    DocumentStructuredKnowledge,
    DocumentType,
    ExtractedEntity,
    ExtractedFact,
    ExtractedObligation,
    FactCategory,
    PDFExtractionResult,
)
from brain.general.contracts.llm import ILLMClient, LLMMessage, LLMRequest

logger = logging.getLogger("brain.extensions.legal.extractor")


class LegalStructuredKnowledgeExtractor:
    """Specialized Legal Domain Extractor for Egyptian Civil Law and commercial contracts."""

    def __init__(self, llm_service: Optional[ILLMClient] = None) -> None:
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

        from brain.general.contracts.llm import LLMRole

        req = LLMRequest(
            messages=(
                LLMMessage(role=LLMRole.SYSTEM, content=system_prompt),
                LLMMessage(
                    role=LLMRole.USER,
                    content=f"Document Filename: {extraction_result.original_filename}\n\nContent:\n{document_text}",
                ),
            ),
            temperature=0.0,
        )

        response = await self.llm_service.complete(req)
        content_str = response.content.strip()
        data = json.loads(content_str)

        facts = [
            ExtractedFact(
                statement=f.get("statement", ""),
                category=FactCategory(f.get("category", "general"))
                if f.get("category") in FactCategory._value2member_map_
                else FactCategory.GENERAL,
                page_number=max(1, int(f.get("page_number", 1))),
                source_excerpt=f.get("source_excerpt", ""),
                confidence=0.95,
            )
            for f in data.get("facts", [])
            if f.get("statement")
        ]

        entities = [
            ExtractedEntity(
                name=e.get("name", ""),
                entity_type=e.get("entity_type", "general"),
                page_number=max(1, int(e.get("page_number", 1))),
                confidence=0.95,
            )
            for e in data.get("entities", [])
            if e.get("name")
        ]

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

        doc_type_val = data.get("document_type", "general_document")
        doc_type = (
            DocumentType(doc_type_val)
            if doc_type_val in DocumentType._value2member_map_
            else DocumentType.GENERAL_DOCUMENT
        )

        return DocumentStructuredKnowledge(
            document_id=extraction_result.document_id,
            document_type=doc_type,
            title=data.get("title") or extraction_result.original_filename,
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
        """Deterministic regex and keyword extractor for legal documents."""
        combined = extraction_result.combined_text
        doc_type = DocumentType.GENERAL_DOCUMENT

        lower_text = combined.lower()
        if "contract" in lower_text or "agreement" in lower_text or "عقد" in lower_text:
            doc_type = DocumentType.CONTRACT
        elif "ruling" in lower_text or "judgment" in lower_text or "حكم" in lower_text or "محكمة" in lower_text:
            doc_type = DocumentType.COURT_RULING
        elif "brief" in lower_text or "memorandum" in lower_text or "مذكرة" in lower_text:
            doc_type = DocumentType.LEGAL_BRIEF
        elif "policy" in lower_text or "regulation" in lower_text or "لائحة" in lower_text:
            doc_type = DocumentType.REGULATORY_POLICY

        facts: list[ExtractedFact] = []
        entities: list[ExtractedEntity] = []
        obligations: list[ExtractedObligation] = []
        parties: list[str] = []

        date_pattern = re.compile(
            r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
        )
        party_pattern = re.compile(
            r"(?:Between|between|Party A|Party B|First Party|Second Party|الطرف الأول|الطرف الثاني)[:\s]+([^\n,.]+)",
            re.IGNORECASE,
        )

        for page in extraction_result.pages:
            p_text = page.text
            p_num = page.page_number

            # Extract parties
            for m in party_pattern.finditer(p_text):
                p_name = m.group(1).strip()
                if len(p_name) > 3 and p_name not in parties:
                    parties.append(p_name)
                    entities.append(
                        ExtractedEntity(
                            name=p_name,
                            entity_type="organization",
                            page_number=p_num,
                            confidence=0.85,
                        )
                    )

            # Extract Egyptian law articles
            article_matches = re.finditer(
                r"(?:المادة|مادة|Article|Law|القانون)\s+(\d+)(?:\s+(?:من|of)?\s+([^\n.]+))?",
                p_text,
                re.IGNORECASE,
            )
            for m in article_matches:
                art_num = m.group(1)
                full_excerpt = m.group(0)
                facts.append(
                    ExtractedFact(
                        statement=f"Cites Article {art_num} of Egyptian Civil Code.",
                        category=FactCategory.LEGAL_FACT,
                        page_number=p_num,
                        source_excerpt=full_excerpt,
                        confidence=0.90,
                    )
                )
                entities.append(
                    ExtractedEntity(
                        name=f"Article {art_num}",
                        entity_type="law_article",
                        page_number=p_num,
                        confidence=0.90,
                    )
                )

            # Obligations (shall, must, will pay, يلتزم, يتعهد)
            obligation_matches = re.finditer(
                r"([^.\n]+(?:shall|must|agrees to|is required to|يلتزم|يتعهد)[^.\n]+(?:\.|\n|$))",
                p_text,
                re.IGNORECASE,
            )
            for m in obligation_matches:
                oblg_text = m.group(1).strip()
                if 20 < len(oblg_text) < 300:
                    obligations.append(
                        ExtractedObligation(
                            description=oblg_text,
                            page_number=p_num,
                        )
                    )
                    facts.append(
                        ExtractedFact(
                            statement=oblg_text,
                            category=FactCategory.OBLIGATION,
                            page_number=p_num,
                            source_excerpt=oblg_text,
                            confidence=0.80,
                        )
                    )

        title = extraction_result.original_filename
        first_line = combined.strip().split("\n")[0].strip() if combined.strip() else ""
        if len(first_line) > 5 and len(first_line) < 120:
            title = first_line

        return DocumentStructuredKnowledge(
            document_id=extraction_result.document_id,
            document_type=doc_type,
            title=title,
            summary=f"Extracted {len(facts)} facts and {len(obligations)} obligations from {extraction_result.page_count} pages.",
            parties=parties,
            entities=entities,
            facts=facts,
            obligations=obligations,
        )
