"""Domain Extensions Package for Brain-Co.

Provides explicit contracts and registration for specialized business verticals
(Legal, Sales, Logistics, etc.) without coupling the General Brain engines.
"""

from app.domains.contracts import IDomainExtension, DomainRegistry, domain_registry
from app.domains.legal.extension import LegalDomainExtension
from app.domains.logistics.extension import LogisticsFleetDomainExtension
from app.domains.sales.extension import SalesDomainExtension

# Auto-register available domain extensions
domain_registry.register(LegalDomainExtension())
domain_registry.register(SalesDomainExtension())
domain_registry.register(LogisticsFleetDomainExtension())

__all__ = [
    "DomainRegistry",
    "IDomainExtension",
    "LegalDomainExtension",
    "LogisticsFleetDomainExtension",
    "SalesDomainExtension",
    "domain_registry",
]
