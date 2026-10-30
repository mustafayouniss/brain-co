"""Pydantic schemas and typed models for Ring 1 PDF ingestion and structured extraction.

Maintains PDF extraction representations while bridging domain schemas from app.domains.legal.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

# Re-export Legal Domain schemas for backward compatibility
from app.domains.legal.schemas import (
    DocumentStructuredKnowledge,
    DocumentType,
    ExtractedEntity,
    ExtractedFact,
    ExtractedObligation,
    FactCategory,
)


class PDFPageContent(BaseModel):
    """Normalized text and metadata for a single extracted PDF page."""

    model_config = ConfigDict(extra="ignore")

    page_number: int = Field(ge=1, description="1-indexed page number in the original PDF")
    text: str = Field(description="Extracted Unicode text content for this page")
    char_count: int = Field(default=0, ge=0, description="Length of text content on this page")
    word_count: int = Field(default=0, ge=0, description="Approximate word count on this page")
    is_blank: bool = Field(default=False, description="True if page contains no non-whitespace text")

    @property
    def character_count(self) -> int:
        return self.char_count

    @property
    def has_text(self) -> bool:
        return not self.is_blank


class PDFExtractionResult(BaseModel):
    """Comprehensive, immutable result of a PDF text extraction operation."""

    model_config = ConfigDict(extra="ignore")

    document_id: str = Field(default_factory=lambda: f"doc-{uuid.uuid4().hex[:12]}")
    original_filename: str
    checksum_sha256: str
    file_size_bytes: int
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
    def total_pages(self) -> int:
        return self.page_count

    @property
    def file_hash(self) -> str:
        return self.checksum_sha256

    @property
    def combined_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)


__all__ = [
    "DocumentStructuredKnowledge",
    "DocumentType",
    "ExtractedEntity",
    "ExtractedFact",
    "ExtractedObligation",
    "FactCategory",
    "PDFExtractionResult",
    "PDFPageContent",
]
