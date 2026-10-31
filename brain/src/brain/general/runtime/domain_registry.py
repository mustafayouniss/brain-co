"""Thread-safe, instantiable Domain Registry for General Brain.

Features a strict two-phase lifecycle:
1. Mutable bootstrap phase: Register and unregister domain extensions.
2. Frozen runtime phase: Once frozen via .freeze(), the registry becomes an immutable
   snapshot with lock-free, zero-contention reads. Further registrations raise an error.

Contains ZERO global mutable singletons or import-time side effects.
"""

from __future__ import annotations

import threading
from types import MappingProxyType
from typing import Optional

from brain.general.contracts.domain import IDomainExtension
from brain.general.contracts.errors import (
    DuplicateDomainRegistrationError,
    RegistryFrozenError,
)

DomainRegistryError = Exception
DomainRegistryLockedError = RegistryFrozenError


class DomainRegistry:
    """Instantiable registry for discovering and managing domain extensions.
    
    Contains NO global state. The application or test instantiates and configures
    its own registry instances.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._domains: dict[str, IDomainExtension] = {}
        self._frozen: bool = False
        self._snapshot: Optional[MappingProxyType] = None

    def register(self, extension: IDomainExtension, *, replace: bool = False) -> None:
        """Register a domain extension during the bootstrap phase.
        
        Args:
            extension: Concrete instance implementing IDomainExtension.
            replace: If True, allows replacing an existing domain_id. Default False.
            
        Raises:
            RegistryFrozenError: If registry is frozen.
            DuplicateDomainRegistrationError: If domain_id already registered and replace=False.
            ValueError: If domain_id is empty.
        """
        with self._lock:
            if self._frozen:
                raise RegistryFrozenError(
                    "Cannot register domain: registry has been frozen for runtime execution."
                )

            d_id = extension.domain_id.lower().strip()
            if not d_id:
                raise ValueError("extension.domain_id cannot be empty")

            if d_id in self._domains and not replace:
                existing = self._domains[d_id]
                raise DuplicateDomainRegistrationError(
                    f"Domain '{d_id}' is already registered ({existing.display_name}). "
                    f"Set replace=True to explicitly overwrite."
                )

            self._domains[d_id] = extension

    def unregister(self, domain_id: str) -> Optional[IDomainExtension]:
        """Unregister a domain extension during bootstrap.
        
        Raises:
            RegistryFrozenError: If registry is frozen.
        """
        with self._lock:
            if self._frozen:
                raise RegistryFrozenError(
                    "Cannot unregister domain: registry has been frozen for runtime execution."
                )
            return self._domains.pop(domain_id.lower().strip(), None)

    def freeze(self) -> None:
        """Lock the registry, creating an immutable snapshot for safe concurrent runtime reads."""
        with self._lock:
            self._frozen = True
            self._snapshot = MappingProxyType(dict(self._domains))

    @property
    def is_frozen(self) -> bool:
        """Return True if registry is frozen."""
        return self._frozen

    def snapshot(self) -> MappingProxyType:
        """Return the immutable snapshot of registered domains.
        
        If not frozen yet, returns a read-only view of the current state.
        """
        with self._lock:
            if self._snapshot is not None:
                return self._snapshot
            return MappingProxyType(dict(self._domains))

    def has_domain(self, domain_id: str) -> bool:
        """Check if a domain identifier is registered."""
        normalized = domain_id.lower().strip()
        if self._frozen and self._snapshot is not None:
            return normalized in self._snapshot
        with self._lock:
            return normalized in self._domains

    def get(self, domain_id: str) -> Optional[IDomainExtension]:
        """Lock-free concurrent lookup by domain identifier."""
        normalized = domain_id.lower().strip()
        if self._frozen and self._snapshot is not None:
            return self._snapshot.get(normalized)
        with self._lock:
            return self._domains.get(normalized)

    def list_domains(self) -> list[str]:
        """Lock-free concurrent listing of registered domain identifiers."""
        if self._frozen and self._snapshot is not None:
            return sorted(list(self._snapshot.keys()))
        with self._lock:
            return sorted(list(self._domains.keys()))

    def clear(self) -> None:
        """Clear all registered domains. Allowed only during mutable bootstrap phase."""
        with self._lock:
            if self._frozen:
                raise RegistryFrozenError("Cannot clear registry: registry is frozen.")
            self._domains.clear()
            self._snapshot = None
