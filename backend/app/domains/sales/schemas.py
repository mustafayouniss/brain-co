"""Sales Domain Schemas and Models.

Defines enterprise sales and CRM domain concepts:
- Deal stages and lead qualifications
- Customer requirements and objections
- Commercial opportunities and competitor mentions
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class DealStage(str, Enum):
    """B2B Sales pipeline deal stages."""

    LEAD = "lead"
    QUALIFICATION = "qualification"
    DISCOVERY = "discovery"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class ObjectionCategory(str, Enum):
    """Customer objection classifications."""

    PRICING = "pricing"
    BUDGET = "budget"
    COMPETITOR = "competitor"
    AUTHORITY = "authority"
    TIMING = "timing"
    TECHNICAL_FIT = "technical_fit"
    SECURITY = "security"


class CustomerRequirement(BaseModel):
    """Specific feature or functional requirement raised by customer."""

    model_config = ConfigDict(extra="ignore")

    requirement_id: str = Field(default_factory=lambda: f"req-{uuid.uuid4().hex[:8]}")
    description: str
    priority: str = Field(default="must_have", pattern="^(must_have|nice_to_have|blocker)$")
    stakeholder: Optional[str] = None


class ExtractedObjection(BaseModel):
    """Sales objection or friction point identified in conversation."""

    model_config = ConfigDict(extra="ignore")

    objection_id: str = Field(default_factory=lambda: f"obj-{uuid.uuid4().hex[:8]}")
    statement: str
    category: ObjectionCategory = ObjectionCategory.PRICING
    competitor_mentioned: Optional[str] = None
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class SalesOpportunity(BaseModel):
    """Structured commercial opportunity representation."""

    model_config = ConfigDict(extra="ignore")

    opportunity_id: str = Field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    account_name: str
    deal_stage: DealStage = DealStage.DISCOVERY
    estimated_arr_usd: Optional[float] = None
    requirements: list[CustomerRequirement] = Field(default_factory=list)
    objections: list[ExtractedObjection] = Field(default_factory=list)
    summary: str = ""
