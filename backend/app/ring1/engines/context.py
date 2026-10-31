"""Compatibility shim for ContextEngine.

Re-exports canonical ContextEngine preserving exact class identity.
"""

from brain.general.engines.context import ContextEngine

__all__ = ["ContextEngine"]
