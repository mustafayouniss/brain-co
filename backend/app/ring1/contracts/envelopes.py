"""Compatibility shim for mesh envelopes.

Re-exports canonical envelopes from brain.general.contracts.envelopes.
"""

from brain.general.contracts.envelopes import (
    PROTOCOL_VERSION,
    DelegationConstraints,
    MeshConstraints,
    MeshError,
    MeshRequest,
    MeshResponse,
    MessageType,
    ResultStatus,
)

__all__ = [
    "PROTOCOL_VERSION",
    "DelegationConstraints",
    "MeshConstraints",
    "MeshError",
    "MeshRequest",
    "MeshResponse",
    "MessageType",
    "ResultStatus",
]
