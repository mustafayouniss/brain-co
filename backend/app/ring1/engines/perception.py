"""Compatibility shim for PerceptionEngine.

Re-exports canonical PerceptionEngine preserving exact class identity.
"""

from brain.general.engines.perception import PerceptionEngine

__all__ = ["PerceptionEngine"]
