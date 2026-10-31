"""Brain-Co Domain Extensions Package."""

from brain.extensions.legal.extension import LegalDomainExtension
from brain.extensions.logistics.extension import LogisticsFleetDomainExtension
from brain.extensions.sales.extension import SalesDomainExtension

__all__ = [
    "LegalDomainExtension",
    "LogisticsFleetDomainExtension",
    "SalesDomainExtension",
]
