"""
Tests for raw storage abstraction and LocalStorageBackend.
"""
from pathlib import Path
import pytest

from orgbrain_ingest.ingestion.errors import StorageError
from orgbrain_ingest.storage.local import LocalStorageBackend


def test_storage_mode(local_storage: LocalStorageBackend):
    assert local_storage.storage_mode == "local"


def test_store_and_retrieve_exact_bytes(local_storage: LocalStorageBackend):
    content = b"PDF or raw document bytes to be verified."
    key = "sources/test-uuid/document.pdf"
    
    stored_key = local_storage.store(content, key)
    assert stored_key == key
    # Ensure logical key is returned, not an absolute path
    assert not Path(stored_key).is_absolute()
    assert "sources/test-uuid/document.pdf" in stored_key

    # Retrieve and verify exact byte match
    retrieved = local_storage.retrieve(stored_key)
    assert retrieved == content


def test_exists_check(local_storage: LocalStorageBackend):
    key = "sources/id-123/sample.txt"
    assert not local_storage.exists(key)
    
    local_storage.store(b"hello world", key)
    assert local_storage.exists(key)


def test_missing_object_raises_storage_error(local_storage: LocalStorageBackend):
    with pytest.raises(StorageError, match="Object not found"):
        local_storage.retrieve("sources/nonexistent/file.txt")


def test_path_traversal_blocked(local_storage: LocalStorageBackend):
    malicious_key = "../../../etc/passwd"
    with pytest.raises(StorageError, match="Path traversal detected"):
        local_storage.store(b"malicious", malicious_key)

    with pytest.raises(StorageError, match="Path traversal detected"):
        local_storage.retrieve(malicious_key)


def test_empty_key_raises_storage_error(local_storage: LocalStorageBackend):
    with pytest.raises(StorageError, match="Storage key cannot be empty"):
        local_storage.store(b"data", "")
