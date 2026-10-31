"""Compatibility shim for engine protocols and results.

Re-exports canonical engine protocols from brain.general.contracts.protocols.
"""

from brain.general.contracts.protocols import (
    EngineResult,
    IContextEngine,
    IMemoryEngine,
    IObservationEngine,
    IPerceptionEngine,
    IPlanningEngine,
    IRetrievalEngine,
    ObservationFeedResult,
)

__all__ = [
    "EngineResult",
    "IContextEngine",
    "IMemoryEngine",
    "IObservationEngine",
    "IPerceptionEngine",
    "IPlanningEngine",
    "IRetrievalEngine",
    "ObservationFeedResult",
]
