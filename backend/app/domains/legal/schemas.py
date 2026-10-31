"""Compatibility shim for Legal Domain Schemas.

Re-exports canonical schemas from brain.extensions.legal.schemas.
"""

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
