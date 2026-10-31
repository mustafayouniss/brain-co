"""Logistics Domain Schemas and Models (Fictional New Domain).

Demonstrates complete General Brain independence from business verticals:
- Maritime fleet vessels and voyage stages
- Cargo inspections, hazardous materials, and customs manifests
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class VoyageStage(str, Enum):
    """Vessel voyage progression stages."""

    DOCKED = "docked"
    UNDERWAY = "underway"
    ANCHORED = "anchored"
    DISCHARGING = "discharging"
    COMPLETED = "completed"


class CargoInspection(BaseModel):
    """Port customs and safety inspection record."""

    model_config = ConfigDict(extra="ignore")

    inspection_id: str = Field(default_factory=lambda: f"insp-{uuid.uuid4().hex[:8]}")
    cargo_type: str
    tonnage_metric: float
    has_hazardous_materials: bool = False
    defects_detected: list[str] = Field(default_factory=list)


class VoyageManifest(BaseModel):
    """Structured maritime voyage manifest."""

    model_config = ConfigDict(extra="ignore")

    manifest_id: str = Field(default_factory=lambda: f"mnf-{uuid.uuid4().hex[:8]}")
    vessel_imo: str
    vessel_name: str
    departure_port: str
    arrival_port: str
    voyage_stage: VoyageStage = VoyageStage.UNDERWAY
    inspections: list[CargoInspection] = Field(default_factory=list)
    summary: str = ""


__all__ = [
    "CargoInspection",
    "VoyageManifest",
    "VoyageStage",
]
