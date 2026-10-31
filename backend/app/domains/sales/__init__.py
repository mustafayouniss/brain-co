"""Compatibility shim for sales domain package."""

from brain.extensions.sales import (
    CustomerRequirement,
    DealStage,
    ExtractedObjection,
    ObjectionCategory,
    SalesConversationExtractor,
    SalesDomainExtension,
    SalesOpportunity,
)

__all__ = [
    "CustomerRequirement",
    "DealStage",
    "ExtractedObjection",
    "ObjectionCategory",
    "SalesConversationExtractor",
    "SalesDomainExtension",
    "SalesOpportunity",
]
