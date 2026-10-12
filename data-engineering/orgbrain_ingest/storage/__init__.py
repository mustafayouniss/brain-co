"""
Storage abstraction package.
"""
from orgbrain_ingest.storage.base import RawStorageBackend
from orgbrain_ingest.storage.local import LocalStorageBackend

__all__ = ["RawStorageBackend", "LocalStorageBackend"]
