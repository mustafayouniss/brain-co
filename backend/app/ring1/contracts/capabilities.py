"""Capability names and registry for the Ring 1 engine mesh.

Each engine registers its capabilities at startup. The mesh router uses
the registry to validate, discover, and dispatch requests. Capability
names follow the pattern ``engine_name.action_name``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


# ---------------------------------------------------------------------------
# Stable capability name constants
# ---------------------------------------------------------------------------

# Perception
PERCEPTION_STRUCTURE_INPUT = "perception.structure_input"

# Observation
OBSERVATION_RECORD_EVENT = "observation.record_event"

# Context
CONTEXT_RESOLVE = "context.resolve"

# Memory
MEMORY_STORE_RECORD = "memory.store_record"
MEMORY_GET_RECORD = "memory.get_record"

# Retrieval
RETRIEVAL_QUERY = "retrieval.query"

# Planning
PLANNING_CREATE_PLAN = "planning.create_plan"
PLANNING_REQUEST_REPLAN = "planning.request_replan"
PLANNING_GET_PLAN_STATUS = "planning.get_plan_status"

# Full allowlist of all Ring 1 capabilities
ALL_CAPABILITIES: frozenset[str] = frozenset({
    PERCEPTION_STRUCTURE_INPUT,
    OBSERVATION_RECORD_EVENT,
    CONTEXT_RESOLVE,
    MEMORY_STORE_RECORD,
    MEMORY_GET_RECORD,
    RETRIEVAL_QUERY,
    PLANNING_CREATE_PLAN,
    PLANNING_REQUEST_REPLAN,
    PLANNING_GET_PLAN_STATUS,
})


# ---------------------------------------------------------------------------
# Registry entry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilityEntry:
    """Metadata for a registered capability."""

    capability_name: str
    engine_name: str
    description: str = ""


# ---------------------------------------------------------------------------
# Capability registry (in-process singleton)
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """Central registry mapping capability names to engine handlers.

    The registry validates capability names against the allowed set and
    provides lookup for the mesh router. It does NOT become a workflow
    controller — it is purely a discovery and dispatch directory.
    """

    def __init__(self) -> None:
        self._entries: dict[str, CapabilityEntry] = {}
        self._handlers: dict[str, Callable] = {}

    def register(
        self,
        capability_name: str,
        engine_name: str,
        handler: Callable,
        description: str = "",
    ) -> None:
        """Register a capability handler for a given capability name.

        Args:
            capability_name: Must be in ALL_CAPABILITIES.
            engine_name: The owning engine's identifier.
            handler: An async callable that accepts a MeshRequest and returns a MeshResponse.
            description: Human-readable description for tracing/logging.

        Raises:
            ValueError: If the capability name is not in the allowed set or is already registered.
        """
        if capability_name not in ALL_CAPABILITIES:
            raise ValueError(
                f"Unknown capability '{capability_name}'. "
                f"Allowed: {sorted(ALL_CAPABILITIES)}"
            )
        if capability_name in self._entries:
            raise ValueError(
                f"Capability '{capability_name}' already registered "
                f"by engine '{self._entries[capability_name].engine_name}'."
            )
        self._entries[capability_name] = CapabilityEntry(
            capability_name=capability_name,
            engine_name=engine_name,
            description=description,
        )
        self._handlers[capability_name] = handler

    def lookup(self, capability_name: str) -> Optional[Callable]:
        """Return the handler for a capability, or None if not registered."""
        return self._handlers.get(capability_name)

    # Alias for lookup
    get_handler = lookup


    def get_entry(self, capability_name: str) -> Optional[CapabilityEntry]:
        """Return the metadata entry for a capability."""
        return self._entries.get(capability_name)

    def is_registered(self, capability_name: str) -> bool:
        return capability_name in self._entries

    def list_capabilities(self) -> list[str]:
        """Return sorted list of registered capability names."""
        return sorted(self._entries.keys())

    def list_engine_capabilities(self, engine_name: str) -> list[str]:
        """Return capabilities registered by a specific engine."""
        return sorted(
            name for name, entry in self._entries.items()
            if entry.engine_name == engine_name
        )

    def clear(self) -> None:
        """Remove all registrations (used in tests)."""
        self._entries.clear()
        self._handlers.clear()
