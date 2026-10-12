"""
SHA-256 fingerprinting utility for raw source files.
"""
import hashlib
from typing import BinaryIO


def calculate_sha256(data: bytes | BinaryIO) -> str:
    """Calculate SHA-256 hex digest for bytes or binary stream.

    Parameters
    ----------
    data : bytes | BinaryIO
        The raw bytes or file-like object to hash.

    Returns
    -------
    str
        64-character lowercase hexadecimal SHA-256 hash.
    """
    hasher = hashlib.sha256()

    if isinstance(data, (bytes, bytearray, memoryview)):
        hasher.update(data)
    else:
        # Stream in chunks
        chunk_size = 64 * 1024
        # Save position if seekable
        seekable = hasattr(data, "seek") and hasattr(data, "tell")
        orig_pos = data.tell() if seekable else None

        while chunk := data.read(chunk_size):
            hasher.update(chunk)

        if seekable and orig_pos is not None:
            data.seek(orig_pos)

    return hasher.hexdigest()
