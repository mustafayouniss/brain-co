"""Tests verifying explicit storage injection and rejection of missing stores."""

from __future__ import annotations

import pytest

from brain.general.contracts.errors import StorageConfigurationError
from brain.general.engines import (
    ObservationEngine,
    BasicMemoryEngine,
    BasicRetrievalEngine,
)
from brain.general.stores import (
    InMemoryObservationStore,
    InMemoryMemoryStore,
    InMemoryRetrievalStore,
)


def test_missing_store_raises_storage_configuration_error():
    """Verify that omitting a store fails immediately with StorageConfigurationError."""
    # ObservationEngine
    with pytest.raises(StorageConfigurationError) as exc_obs:
        ObservationEngine(store=None)
    assert "store" in str(exc_obs.value).lower()

    # BasicMemoryEngine
    with pytest.raises(StorageConfigurationError) as exc_mem:
        BasicMemoryEngine(store=None)
    assert "store" in str(exc_mem.value).lower()

    # BasicRetrievalEngine
    with pytest.raises(StorageConfigurationError) as exc_ret:
        BasicRetrievalEngine(store=None)
    assert "store" in str(exc_ret.value).lower()


def test_no_silent_in_memory_fallback():
    """Constructing an engine with no arguments must raise StorageConfigurationError, never silently fall back."""
    with pytest.raises(StorageConfigurationError):
        ObservationEngine()

    with pytest.raises(StorageConfigurationError):
        BasicMemoryEngine()

    with pytest.raises(StorageConfigurationError):
        BasicRetrievalEngine()


def test_explicit_store_injection_succeeds():
    """Explicitly injecting storage implementations succeeds."""
    obs_store = InMemoryObservationStore()
    obs_engine = ObservationEngine(store=obs_store)
    assert obs_engine._store is obs_store

    mem_store = InMemoryMemoryStore()
    mem_engine = BasicMemoryEngine(store=mem_store)
    assert mem_engine._store is mem_store

    ret_store = InMemoryRetrievalStore(memory_store=mem_store)
    ret_engine = BasicRetrievalEngine(store=ret_store)
    assert ret_engine._store is ret_store
