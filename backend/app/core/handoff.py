"""Compatibility shim for HandoffPolicy.

Re-exports canonical HandoffPolicy from brain.general.policies.handoff.
"""

from brain.general.policies.handoff import (
    HandoffPolicy,
    HandoffRejectionReason,
    HandoffValidationResult,
)

__all__ = [
    "HandoffPolicy",
    "HandoffRejectionReason",
    "HandoffValidationResult",
]
