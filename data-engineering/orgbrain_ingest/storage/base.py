"""
Abstract raw storage backend interface.
"""
from abc import ABC, abstractmethod


class RawStorageBackend(ABC):
    """Abstract interface for raw document file storage.

    Decouples the ingestion pipeline from specific storage media
    (Local filesystem, S3, MinIO, Azure Blob, etc.).
    """

    @property
    @abstractmethod
    def storage_mode(self) -> str:
        """Return the storage mode identifier (e.g. 'local', 's3', 'minio')."""
        pass

    @abstractmethod
    def store(self, content: bytes, destination_key: str) -> str:
        """Store raw bytes at destination_key.

        Parameters
        ----------
        content : bytes
            Raw binary content to store.
        destination_key : str
            Logical key or path where content should be stored.

        Returns
        -------
        str
            The authoritative storage key / reference.

        Raises
        ------
        StorageError
            If storing the content fails.
        """
        pass

    @abstractmethod
    def retrieve(self, storage_key: str) -> bytes:
        """Retrieve raw bytes by storage key.

        Parameters
        ----------
        storage_key : str
            The key returned during store().

        Returns
        -------
        bytes
            The raw stored bytes.

        Raises
        ------
        StorageError
            If reading the content fails or key does not exist.
        """
        pass

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """Check whether a storage key exists.

        Parameters
        ----------
        storage_key : str
            The key to check.

        Returns
        -------
        bool
            True if the object exists, False otherwise.
        """
        pass
