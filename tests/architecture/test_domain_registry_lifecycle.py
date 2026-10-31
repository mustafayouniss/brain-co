"""Tests verifying DomainRegistry lifecycle: bootstrap, registration, freeze, and runtime snapshot."""

from __future__ import annotations

import concurrent.futures
import pytest

from brain.general.contracts.domain import IDomainExtension
from brain.general.contracts.errors import (
    DuplicateDomainRegistrationError,
    RegistryFrozenError,
)
from brain.general.runtime.domain_registry import DomainRegistry


class DummyExtension(IDomainExtension):
    def __init__(self, domain_id: str, display_name: str = "Dummy"):
        self._domain_id = domain_id
        self._display_name = display_name

    @property
    def domain_id(self) -> str:
        return self._domain_id

    @property
    def display_name(self) -> str:
        return self._display_name

    def register_capabilities(self, registry) -> None:
        pass

    def get_schemas(self) -> dict:
        return {}

    async def extract_domain_knowledge(self, raw_content, context, metadata=None) -> dict:
        return {"status": "ok"}


def test_domain_registry_bootstrap_and_normalization():
    registry = DomainRegistry()

    # Normalized casing & whitespace
    ext = DummyExtension("  LeGaL  ")
    registry.register(ext)

    assert registry.has_domain("legal")
    assert registry.has_domain("LEGAL")
    assert registry.has_domain("  legal  ")
    retrieved = registry.get("legal")
    assert retrieved is ext


def test_reject_empty_domain_id():
    registry = DomainRegistry()
    ext = DummyExtension("   ")
    with pytest.raises(ValueError):
        registry.register(ext)


def test_duplicate_registration_rejected_by_default():
    registry = DomainRegistry()
    ext1 = DummyExtension("legal")
    ext2 = DummyExtension("LEGAL")

    registry.register(ext1)
    with pytest.raises(DuplicateDomainRegistrationError):
        registry.register(ext2)


def test_explicit_replacement():
    registry = DomainRegistry()
    ext1 = DummyExtension("legal", "Old Legal")
    ext2 = DummyExtension("legal", "New Legal")

    registry.register(ext1)
    registry.register(ext2, replace=True)

    assert registry.get("legal").display_name == "New Legal"


def test_unregister_domain():
    registry = DomainRegistry()
    ext = DummyExtension("sales")
    registry.register(ext)
    assert registry.has_domain("sales")

    removed = registry.unregister("sales")
    assert removed is ext
    assert not registry.has_domain("sales")
    assert registry.get("sales") is None


def test_freeze_lifecycle_and_mutation_prevention():
    registry = DomainRegistry()
    ext = DummyExtension("logistics")
    registry.register(ext)

    assert not registry.is_frozen
    registry.freeze()
    assert registry.is_frozen

    # Snapshot is immutable
    snapshot = registry.snapshot()
    with pytest.raises(TypeError):
        snapshot["new_key"] = ext  # type: ignore

    # Mutations after freeze MUST raise RegistryFrozenError
    with pytest.raises(RegistryFrozenError):
        registry.register(DummyExtension("finance"))

    with pytest.raises(RegistryFrozenError):
        registry.register(DummyExtension("logistics"), replace=True)

    with pytest.raises(RegistryFrozenError):
        registry.unregister("logistics")

    # Reads continue to work
    assert registry.has_domain("logistics")
    assert registry.get("logistics") is ext


def test_concurrent_bootstrap_access():
    registry = DomainRegistry()

    def register_ext(idx: int):
        ext = DummyExtension(f"domain_{idx}")
        registry.register(ext)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(register_ext, i) for i in range(50)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    assert len(registry.list_domains()) == 50
    registry.freeze()
    assert len(registry.snapshot()) == 50
