"""Legal Domain Extension for Brain-Co."""

from brain.extensions.legal.extension import LegalDomainExtension
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
