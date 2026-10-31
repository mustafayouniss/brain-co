"""Compatibility shim for Domain Extension Contracts and Registry.

Re-exports canonical contracts from:
- brain.general.contracts.domain.IDomainExtension
- brain.general.runtime.domain_registry.DomainRegistry
"""

from brain.general.contracts.domain import IDomainExtension
from brain.general.runtime.domain_registry import (
    DomainRegistry as CanonicalDomainRegistry,
    DomainRegistryLockedError,
    DuplicateDomainRegistrationError,
)


class DomainRegistry(CanonicalDomainRegistry):
    """Legacy compatibility adapter for DomainRegistry allowing idempotent re-registration."""

    def register(self, extension: IDomainExtension, *, replace: bool = True) -> None:
        super().register(extension, replace=replace)


# Global domain registry instance for legacy backward compatibility
domain_registry = DomainRegistry()

__all__ = [
    "DomainRegistry",
    "DomainRegistryLockedError",
    "DuplicateDomainRegistrationError",
    "IDomainExtension",
    "domain_registry",
]
