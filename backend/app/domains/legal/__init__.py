"""Compatibility shim for legal domain package."""

from brain.extensions.legal import (
    DocumentStructuredKnowledge,
    DocumentType,
    ExtractedEntity,
    ExtractedFact,
    ExtractedObligation,
    FactCategory,
    LegalDomainExtension,
    LegalStructuredKnowledgeExtractor,
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
    "LegalDomainExtension",
    "LegalStructuredKnowledgeExtractor",
    "PDFExtractionResult",
    "PDFPageContent",
]
