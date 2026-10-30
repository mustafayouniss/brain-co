"""Legal Domain Schemas and Models.

Defines Egyptian Civil Law and legal contract domain models:
- Document types (contracts, court rulings, legal briefs)
- Fact categories and legal obligations
- Extracted legal entities, facts, and structured knowledge
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Legal document classifications."""

    CONTRACT = "contract"
    LEGAL_BRIEF = "legal_brief"
    COURT_RULING = "court_ruling"
    REGULATORY_POLICY = "regulatory_policy"
    CORPORATE_DOCUMENT = "corporate_document"
    CORRESPONDENCE = "correspondence"
    GENERAL_DOCUMENT = "general_document"


class FactCategory(str, Enum):
    """Categories of legal and operational facts."""

    LEGAL_FACT = "legal_fact"
    OBLIGATION = "obligation"
    DEADLINE = "deadline"
    FINANCIAL = "financial"
    IDENTITY = "identity"
    GOVERNANCE = "governance"
    GENERAL = "general"


class ExtractedEntity(BaseModel):
    """Legal entity (person, law firm, corporation, court, statutory article)."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(description="Name of the entity (person, organization, court, location, etc.)")
    entity_type: str = Field(description="Type: person, organization, court, law, location, date")
    page_number: int = Field(ge=1, description="Page number where the entity appears")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ExtractedFact(BaseModel):
    """Legal fact with source provenance."""

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
    """Legal or contractual duty or obligation."""

    model_config = ConfigDict(extra="ignore")

    obligation_id: str = Field(default_factory=lambda: f"oblg-{uuid.uuid4().hex[:8]}")
    description: str = Field(description="Description of legal or contractual obligation")
    responsible_party: Optional[str] = None
    deadline: Optional[str] = None
    page_number: int = Field(ge=1)


class DocumentStructuredKnowledge(BaseModel):
    """Structured knowledge representation of a legal document."""

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
