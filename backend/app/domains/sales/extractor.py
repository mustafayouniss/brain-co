"""Compatibility shim for SalesConversationExtractor.

Re-exports canonical extractor from brain.extensions.sales.extractor.
"""

from brain.extensions.sales.extractor import SalesConversationExtractor

__all__ = ["SalesConversationExtractor"]
