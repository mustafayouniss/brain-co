"""Compatibility shim for ContextRef and ResolutionStatus.

Re-exports canonical contracts from brain.general.contracts.context_ref.
"""

from brain.general.contracts.context_ref import ContextRef, ResolutionStatus

__all__ = ["ContextRef", "ResolutionStatus"]
