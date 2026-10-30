"""Sales Conversation and Deal Signal Extractor."""

from __future__ import annotations

import re
from typing import Any, Optional

from app.domains.sales.schemas import (
    CustomerRequirement,
    DealStage,
    ExtractedObjection,
    ObjectionCategory,
    SalesOpportunity,
)


class SalesConversationExtractor:
    """Extracts customer requirements, objections, and deal signals from text/conversations."""

    def extract(self, text: str, account_name: str = "Prospective Client") -> SalesOpportunity:
        """Analyze text to identify sales requirements, objections, and pricing signals."""
        requirements: list[CustomerRequirement] = []
        objections: list[ExtractedObjection] = []
        stage = DealStage.DISCOVERY

        lower = text.lower()

        # Requirement patterns: "need to", "must have", "require", "looking for"
        req_matches = re.finditer(r"(?:need to|must have|require|looking for|we want)\s+([^.\n]+)", text, re.IGNORECASE)
        for m in req_matches:
            statement = m.group(1).strip()
            if len(statement) > 5:
                requirements.append(
                    CustomerRequirement(
                        description=statement[:200],
                        priority="must_have",
                    )
                )

        # Objection patterns: "too expensive", "budget limit", "competitor", "security concern"
        if "expensive" in lower or "budget" in lower or "cost" in lower:
            objections.append(
                ExtractedObjection(
                    statement="Customer expressed budget constraints or pricing sensitivity.",
                    category=ObjectionCategory.PRICING,
                    severity="high",
                )
            )

        if "security" in lower or "soc2" in lower or "compliance" in lower:
            objections.append(
                ExtractedObjection(
                    statement="Security or enterprise compliance audit requested.",
                    category=ObjectionCategory.SECURITY,
                    severity="medium",
                )
            )

        competitor = None
        for comp in ["salesforce", "hubspot", "oracle", "microsoft"]:
            if comp in lower:
                competitor = comp.capitalize()
                objections.append(
                    ExtractedObjection(
                        statement=f"Competitor mentioned during evaluation: {competitor}",
                        category=ObjectionCategory.COMPETITOR,
                        competitor_mentioned=competitor,
                        severity="medium",
                    )
                )

        if "proposal" in lower or "contract" in lower:
            stage = DealStage.PROPOSAL

        return SalesOpportunity(
            account_name=account_name,
            deal_stage=stage,
            requirements=requirements,
            objections=objections,
            summary=f"Identified {len(requirements)} requirements and {len(objections)} objections.",
        )
