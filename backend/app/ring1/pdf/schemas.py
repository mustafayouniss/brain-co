"""Pydantic schemas and typed models for Ring 1 PDF ingestion and structured extraction.

Re-exports canonical schemas from brain.extensions.legal.schemas for complete backward compatibility.
"""

from __future__ import annotations

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
