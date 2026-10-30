"""Pydantic schemas and typed models for Ring 1 PDF ingestion and structured extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    CONTRACT = "contract"
    LEGAL_BRIEF = "legal_brief"
    COURT_RULING = "court_ruling"
    REGULATORY_POLICY = "regulatory_policy"
    CORPORATE_DOCUMENT = "corporate_document"
    CORRESPONDENCE = "correspondence"
    GENERAL_DOCUMENT = "general_document"


class FactCategory(str, Enum):
    LEGAL_FACT = "legal_fact"
    OBLIGATION = "obligation"
    DEADLINE = "deadline"
    FINANCIAL = "financial"
    IDENTITY = "identity"
    GOVERNANCE = "governance"
    GENERAL = "general"


class ExtractedEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Name of the entity (person, organization, court, location, etc.)")
    entity_type: str = Field(description="Type: person, organization, court, law, location, date")
    page_number: int = Field(ge=1, description="Page number where the entity appears")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedFact(BaseModel):
    model_config = ConfigDict(extra="ignore")

    fact_id: str = Field(default_factory=lambda: f"fact-{uuid.uuid4().hex[:8]}")
    statement: str = Field(description="Concrete factual statement extracted from the document text")
    category: FactCategory = Field(default=FactCategory.GENERAL)
    page_number: int = Field(ge=1, description="Source page number where fact was found")
    source_excerpt: str = Field(description="Direct text excerpt from the document establishing provenance")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_validated: bool = Field(default=False, description="Whether fact has passed validation rules")

    @property
    def fact_text(self) -> str:
        return self.statement

    @property
    def validation_status(self) -> str:
        return "validated" if self.is_validated else "candidate"


class ExtractedObligation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    obligation_id: str = Field(default_factory=lambda: f"oblg-{uuid.uuid4().hex[:8]}")
    description: str = Field(description="Description of legal or contractual obligation")
    responsible_party: Optional[str] = None
    deadline: Optional[str] = None
    page_number: int = Field(ge=1)


class PDFPageContent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    page_number: int = Field(ge=1)
    text: str
    char_count: int
    word_count: int
    is_blank: bool = False


class PDFExtractionResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4().hex[:12]}")
    original_filename: str
    file_size_bytes: int
    checksum_sha256: str
    page_count: int
    total_characters: int
    pages: list[PDFPageContent]
    is_scanned: bool = False
    requires_ocr: bool = False
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    extracted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def file_hash(self) -> str:
        return self.checksum_sha256

    @property
    def combined_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


class DocumentStructuredKnowledge(BaseModel):
    model_config = ConfigDict(extra="ignore")

    document_id: str
    document_type: DocumentType = DocumentType.GENERAL_DOCUMENT
    title: str = "Untitled Document"
    summary: str = ""
    parties: list[str] = Field(default_factory=list)
    dates_and_events: list[dict[str, str]] = Field(default_factory=list)
    entities: list[ExtractedEntity] = Field(default_factory=list)
    facts: list[ExtractedFact] = Field(default_factory=list)
    obligations: list[ExtractedObligation] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    total_facts_count: int = 0
    extraction_mode: str = "deterministic"
