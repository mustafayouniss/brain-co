"""Sales Domain Extension for Brain-Co."""

from brain.extensions.sales.extension import SalesDomainExtension
from brain.extensions.sales.extractor import SalesConversationExtractor
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
    "SalesConversationExtractor",
    "SalesDomainExtension",
    "SalesOpportunity",
]
