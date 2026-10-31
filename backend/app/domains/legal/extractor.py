"""Compatibility shim for LegalStructuredKnowledgeExtractor.

Re-exports and adapts canonical extractor from brain.extensions.legal.extractor.
"""

from typing import Optional

from brain.extensions.legal.extractor import (
    LegalStructuredKnowledgeExtractor as CanonicalExtractor,
)
from brain.general.contracts.llm import ILLMClient


class LegalStructuredKnowledgeExtractor(CanonicalExtractor):
    """Compatibility adapter for LegalStructuredKnowledgeExtractor."""

    def __init__(self, llm_service=None) -> None:
        client = llm_service
        if client is not None and not isinstance(client, ILLMClient):
            try:
                from app.infrastructure.ai.adapter import LLMServiceAdapter
                client = LLMServiceAdapter(client)
            except Exception:
                pass
        super().__init__(llm_service=client)


__all__ = ["LegalStructuredKnowledgeExtractor"]
