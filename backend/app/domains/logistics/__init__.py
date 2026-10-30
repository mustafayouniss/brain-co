"""Logistics domain package (fictional new domain)."""

from app.domains.logistics.extension import LogisticsFleetDomainExtension
from app.domains.logistics.extractor import MaritimeManifestExtractor
from app.domains.logistics.schemas import CargoInspection, VoyageManifest, VoyageStage

__all__ = [
    "CargoInspection",
    "LogisticsFleetDomainExtension",
    "MaritimeManifestExtractor",
    "VoyageManifest",
    "VoyageStage",
]
