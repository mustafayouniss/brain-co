"""Structured Knowledge Extractor for Ring 1 PDF Ingestion.

Bridges to the Legal Domain knowledge extractor (app.domains.legal.extractor)
while preserving the legacy interface for existing pipelines and tests,
avoiding circular imports between domains and pdf package.
"""

from __future__ import annotations

from typing import Any, Optional


class StructuredKnowledgeExtractor:
    """Compatibility wrapper delegating to LegalStructuredKnowledgeExtractor."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        from app.domains.legal.extractor import LegalStructuredKnowledgeExtractor as _Real
        self._delegate = _Real(*args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._delegate, name)

    def extract(self, *args: Any, **kwargs: Any) -> Any:
        return self._delegate.extract(*args, **kwargs)


def get_legal_extractor(*args: Any, **kwargs: Any) -> Any:
    from app.domains.legal.extractor import LegalStructuredKnowledgeExtractor as _Real
    return _Real(*args, **kwargs)


__all__ = [
    "StructuredKnowledgeExtractor",
]
