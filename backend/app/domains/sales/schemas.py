"""Compatibility shim for Sales Domain Schemas.

Re-exports canonical schemas from brain.extensions.sales.schemas.
"""

from brain.extensions.sales.schemas import (
    CustomerRequirement,
    DealStage,
    ExtractedObjection,
    ObjectionCategory,
    SalesOpportunity,
)

__all__ = [
    "CustomerRequirement",
    "DealStage",
    "ExtractedObjection",
    "ObjectionCategory",
    "SalesOpportunity",
]
