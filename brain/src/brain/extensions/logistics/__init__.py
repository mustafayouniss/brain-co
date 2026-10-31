"""Logistics Domain Extension for Brain-Co."""

from brain.extensions.logistics.extension import LogisticsFleetDomainExtension
from brain.extensions.logistics.extractor import MaritimeManifestExtractor
from brain.extensions.logistics.schemas import (
    CargoInspection,
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
