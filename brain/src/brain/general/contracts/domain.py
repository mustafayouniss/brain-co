"""Domain Extension Contract for General Brain.

Establishes the public boundary between the Domain Layer and General Brain.
The General Brain never imports concrete domain modules.
Domain modules consume General Brain protocols and register capabilities into the runtime.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from brain.general.contracts.capabilities import CapabilityRegistry
from brain.general.contracts.context import BrainContext


class IDomainExtension(ABC):
    """Abstract interface that every specialized Domain Module must implement."""

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """Unique domain identifier (e.g. 'legal', 'sales', 'logistics')."""
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
