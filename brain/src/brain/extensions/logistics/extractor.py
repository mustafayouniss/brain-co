"""Maritime Manifest and Cargo Inspection Extractor (Fictional Logistics Domain)."""

from __future__ import annotations

import re
from typing import Any, Optional

from brain.extensions.logistics.schemas import (
    CargoInspection,
    VoyageManifest,
    VoyageStage,
)


class MaritimeManifestExtractor:
    """Extracts shipping vessel, port of call, and hazardous cargo data."""

    def extract(self, text: str, vessel_name: str = "Vessel Unknown") -> VoyageManifest:
        """Parse maritime manifest or shipping log text."""
        lower = text.lower()

        # IMO Number extraction: IMO 1234567
        imo_match = re.search(r"IMO\s*[:#-]?\s*(\d{7})", text, re.IGNORECASE)
        vessel_imo = f"IMO-{imo_match.group(1)}" if imo_match else "IMO-0000000"

        # Ports
        departure = "Port of Alexandria"
        arrival = "Port of Rotterdam"
        dep_match = re.search(r"(?:origin|departure|from)\s*[:]?\s*([A-Za-z\s]+?)(?:,|\sto|\sand|\n|$)", text, re.IGNORECASE)
        arr_match = re.search(r"(?:destination|arrival|to)\s*[:]?\s*([A-Za-z\s]+?)(?:,|\sfrom|\sand|\n|$)", text, re.IGNORECASE)
        if dep_match and len(dep_match.group(1).strip()) > 2:
            departure = dep_match.group(1).strip()
        if arr_match and len(arr_match.group(1).strip()) > 2:
            arrival = arr_match.group(1).strip()

        # Stage
        stage = VoyageStage.UNDERWAY
        if "docked" in lower or "berth" in lower:
            stage = VoyageStage.DOCKED
        elif "discharg" in lower or "unloading" in lower:
            stage = VoyageStage.DISCHARGING
        elif "anchor" in lower:
            stage = VoyageStage.ANCHORED

        # Cargo inspections
        inspections: list[CargoInspection] = []
        is_hazardous = any(k in lower for k in ["hazmat", "hazardous", "class 3", "flammable", "toxic", "chemical"])
        defects = []
        if "leak" in lower:
            defects.append("Container seal compromised / fluid leakage")
        if "damaged" in lower:
            defects.append("Physical packaging damage noted")

        tonnage = 1250.0
        tonnage_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mt|tons|metric tons)", text, re.IGNORECASE)
        if tonnage_match:
            try:
                tonnage = float(tonnage_match.group(1))
            except ValueError:
                pass

        cargo_type = "Containerized Dry Bulk"
        if "crude" in lower or "oil" in lower:
            cargo_type = "Liquid Bulk / Petroleum"
        elif "reefer" in lower or "perishable" in lower or "food" in lower:
            cargo_type = "Refrigerated Perishables"

        inspections.append(
            CargoInspection(
                cargo_type=cargo_type,
                tonnage_metric=tonnage,
                has_hazardous_materials=is_hazardous,
                defects_detected=defects,
            )
        )

        return VoyageManifest(
            vessel_imo=vessel_imo,
            vessel_name=vessel_name,
            departure_port=departure,
            arrival_port=arrival,
            voyage_stage=stage,
            inspections=inspections,
            summary=f"Manifest parsed: {vessel_name} [{vessel_imo}] {stage.value} from {departure} to {arrival}.",
        )


__all__ = ["MaritimeManifestExtractor"]
