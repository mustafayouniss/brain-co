"""Domain Extension Contracts and Registry for Brain-Co.

Establishes the public boundary between the Domain Layer and the General Brain.
The General Brain never imports concrete domain modules.
Domain modules consume General Brain protocols and register capabilities via DomainRegistry.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional

from app.core.context import BrainContext
from app.ring1.contracts.capabilities import CapabilityRegistry


class IDomainExtension(ABC):
    """Abstract interface that every specialized Domain Module must implement."""

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Unique domain identifier (e.g. 'legal', 'sales', 'hr', 'logistics')."""
        ...

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable domain name."""
        ...

    @property
    def version(self) -> str:
        """Domain module version."""
        return "1.0.0"

    @abstractmethod
    def register_capabilities(self, registry: CapabilityRegistry) -> None:
        """Register domain-specific capabilities into the CapabilityRegistry."""
        ...

    @abstractmethod
    def get_schemas(self) -> dict[str, Any]:
        """Return domain-specific schemas, entities, and validation rules."""
        ...

    @abstractmethod
    async def extract_domain_knowledge(
        self,
        raw_content: Any,
        context: BrainContext,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Perform domain-specific knowledge extraction and interpretation."""
        ...


class DomainRegistry:
    """Thread-safe registry for discovering and managing domain extensions."""

    def __init__(self) -> None:
        self._domains: dict[str, IDomainExtension] = {}

    def register(self, domain: IDomainExtension) -> None:
        """Register a new domain extension."""
        d_id = domain.domain_id.lower().strip()
        self._domains[d_id] = domain

    def get(self, domain_id: str) -> Optional[IDomainExtension]:
        """Retrieve a domain extension by its identifier."""
        return self._domains.get(domain_id.lower().strip())

    def list_domains(self) -> list[str]:
        """List all registered domain identifiers."""
        return sorted(list(self._domains.keys()))

    def unregister(self, domain_id: str) -> None:
        """Unregister a domain extension."""
        self._domains.pop(domain_id.lower().strip(), None)

    def reset(self) -> None:
        """Clear all registered domains (used in testing)."""
        self._domains.clear()


# Global domain registry singleton
domain_registry = DomainRegistry()
