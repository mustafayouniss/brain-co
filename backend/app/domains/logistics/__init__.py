"""Compatibility shim for logistics domain package."""

from brain.extensions.logistics import (
    CargoInspection,
    LogisticsFleetDomainExtension,
    MaritimeManifestExtractor,
    VoyageManifest,
    VoyageStage,
)

__all__ = [
    "CargoInspection",
    "LogisticsFleetDomainExtension",
    "MaritimeManifestExtractor",
    "VoyageManifest",
    "VoyageStage",
]
