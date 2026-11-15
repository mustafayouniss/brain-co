"""Brain-Co Domain Extensions Package."""

from typing import Optional

from brain.extensions.legal.extension import LegalDomainExtension
from brain.extensions.logistics.extension import LogisticsFleetDomainExtension
from brain.extensions.sales.extension import SalesDomainExtension
from brain.general.contracts.domain import IDomainExtension

_EXTENSIONS: dict[str, IDomainExtension] = {
    "legal": LegalDomainExtension(),
    "sales": SalesDomainExtension(),
    "logistics": LogisticsFleetDomainExtension(),
}


def get_domain_extension(domain_id: str) -> Optional[IDomainExtension]:
    """Retrieve the registered domain extension by domain identifier."""
    if not domain_id:
        return None
    return _EXTENSIONS.get(domain_id.strip().lower())


__all__ = [
    "LegalDomainExtension",
    "LogisticsFleetDomainExtension",
    "SalesDomainExtension",
    "get_domain_extension",
]
