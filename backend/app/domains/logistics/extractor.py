"""Compatibility shim for MaritimeManifestExtractor.

Re-exports canonical extractor from brain.extensions.logistics.extractor.
"""

from brain.extensions.logistics.extractor import MaritimeManifestExtractor

__all__ = ["MaritimeManifestExtractor"]
