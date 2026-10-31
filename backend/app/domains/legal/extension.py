"""Compatibility shim for LegalDomainExtension.

Re-exports canonical LegalDomainExtension from brain.extensions.legal.
"""

from brain.extensions.legal.extension import LegalDomainExtension

__all__ = ["LegalDomainExtension"]
