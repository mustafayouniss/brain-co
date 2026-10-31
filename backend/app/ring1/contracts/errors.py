"""Compatibility shim for EngineErrorCode and storage errors.

Re-exports canonical error contracts from brain.general.contracts.errors.
"""

from brain.general.contracts.errors import (
    EngineErrorCode,
    StorageConfigurationError,
    StorageError,
)

__all__ = [
    "EngineErrorCode",
    "StorageConfigurationError",
    "StorageError",
]
