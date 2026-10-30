"""Cryptographically Signed HMAC Keyset Cursor Pagination.

Binds cursor tokens to the caller's authorized organization, case scope,
canonical filter hash, and sort order. Strictly asserts Base64URL, exact keys,
timezone-aware timestamps, and RFC 4122 UUID syntax before any SQL query.
"""

from __future__ import annotations

import base64
from datetime import datetime
import hashlib
import hmac
import json
from typing import Any, Optional
import uuid
from uuid import UUID

from fastapi import HTTPException, status

from app.core.config import settings

EXPECTED_CURSOR_KEYS = {"v", "org_id", "case_id", "filter_hash", "sort", "created_at", "id"}


def canonical_json(data: dict[str, Any]) -> str:
    """Produce deterministic canonical JSON representation for filter hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def encode_cursor(
    organization_id: str,
    case_id: Optional[str],
    current_filters: dict[str, Any],
    sort_order: str,
    created_at: datetime,
    row_id: UUID,
) -> str:
    """Generate an HMAC-SHA256 signed, Base64URL-encoded pagination cursor."""
    if created_at.tzinfo is None or created_at.tzinfo.utcoffset(created_at) is None:
        raise ValueError("created_at timestamp must be timezone-aware for cursor generation")

    filter_hash = hashlib.sha256(canonical_json(current_filters).encode("utf-8")).hexdigest()

    payload = {
        "v": 1,
        "org_id": organization_id,
        "case_id": case_id or "",
        "filter_hash": filter_hash,
        "sort": sort_order,
        "created_at": created_at.isoformat(),
        "id": str(row_id).lower(),
    }

    raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(raw_bytes).decode("utf-8").rstrip("=")

    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{encoded_payload}.{signature}"


def decode_and_verify_cursor(
    cursor_str: str,
    expected_org_id: str,
    expected_case_id: Optional[str],
    current_filters: dict[str, Any],
    expected_sort: str = "created_at_desc_id_desc",
) -> tuple[datetime, UUID]:
    """Strictly validate HMAC signature and all 7 declared cursor fields before query execution."""
    if not cursor_str or not isinstance(cursor_str, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_FORMAT", "message": "Cursor must be a non-empty string"},
        )

    parts = cursor_str.split(".")
    if len(parts) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_FORMAT", "message": "Cursor token structure is malformed"},
        )

    encoded_payload, signature = parts[0], parts[1]

    # 1. Cryptographic HMAC Check
    expected_sig = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        encoded_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "TAMPERED_CURSOR", "message": "Cursor signature verification failed"},
        )

    # 2. Strict Base64URL Decoding (Reject non-URL safe characters)
    if any(c in encoded_payload for c in "+/ \n\r\t"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MALFORMED_CURSOR_ENCODING", "message": "Non-URL-safe Base64 character detected"},
        )

    try:
        padding = "=" * (-len(encoded_payload) % 4)
        raw_bytes = base64.urlsafe_b64decode((encoded_payload + padding).encode("utf-8"))
        payload = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "MALFORMED_CURSOR_PAYLOAD", "message": f"Failed to decode cursor payload: {exc}"},
        )

    # 3. Reject Missing, Extra, or Unexpected Fields
    if not isinstance(payload, dict) or set(payload.keys()) != EXPECTED_CURSOR_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNEXPECTED_CURSOR_FIELDS", "message": "Cursor payload fields do not match contract"},
        )

    # 4. Strict Type Assertions
    if payload["v"] != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "UNSUPPORTED_CURSOR_VERSION", "message": f"Unsupported version: {payload.get('v')}"},
        )

    # 5. Scope Binding Assertions
    if payload["org_id"] != expected_org_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_SCOPE", "message": "Cursor belongs to a different organization"},
        )

    bound_case = payload.get("case_id") or None
    target_case = expected_case_id or None
    if bound_case != target_case:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_SCOPE", "message": "Cursor belongs to a different case scope"},
        )

    # 6. Canonical Filter & Sort Match
    current_filter_hash = hashlib.sha256(canonical_json(current_filters).encode("utf-8")).hexdigest()
    if payload["filter_hash"] != current_filter_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CURSOR_FILTER_MISMATCH", "message": "Cursor filter parameters do not match query"},
        )

    if payload["sort"] != expected_sort:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CURSOR_SORT_MISMATCH", "message": "Cursor sort order does not match query"},
        )

    # 7. Strict Timezone-Aware ISO8601 Verification
    try:
        cursor_created_at = datetime.fromisoformat(payload["created_at"])
        if cursor_created_at.tzinfo is None or cursor_created_at.tzinfo.utcoffset(cursor_created_at) is None:
            raise ValueError("Timestamp must be timezone-aware")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_TIMESTAMP", "message": f"Malformed ISO8601 timestamp: {exc}"},
        )

    # 8. Strict UUID Syntax & RFC 4122 Variant Verification
    try:
        cursor_id = UUID(payload["id"])
        if cursor_id.variant != uuid.RFC_4122:
            raise ValueError("UUID is not RFC 4122 compliant")
        if str(cursor_id).lower() != payload["id"].lower():
            raise ValueError("UUID string format canonical mismatch")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_CURSOR_UUID", "message": f"Malformed UUID: {exc}"},
        )

    return cursor_created_at, cursor_id
