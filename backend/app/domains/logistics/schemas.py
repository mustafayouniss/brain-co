"""Compatibility shim for Logistics Domain Schemas.

Re-exports canonical schemas from brain.extensions.logistics.schemas.
"""

from brain.extensions.logistics.schemas import (
    CargoInspection,
    VoyageManifest,
    VoyageStage,
)

__all__ = [
    "CargoInspection",
    "VoyageManifest",
    "VoyageStage",
]
