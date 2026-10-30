"""Security and validation tests for cryptographically signed HMAC keyset cursors."""

import base64
from datetime import datetime, timezone
import hashlib
import json
import uuid
from uuid import UUID

from fastapi import HTTPException
import pytest

from app.core.cursor import decode_and_verify_cursor, encode_cursor


def test_cursor_roundtrip_success():
    org_id = "org-test-123"
    case_id = "case-abc-456"
    filters = {"status": "ACTIVE", "category": "LEGAL"}
    sort_order = "created_at_desc_id_desc"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id=case_id,
        current_filters=filters,
        sort_order=sort_order,
        created_at=created_at,
        row_id=row_id,
    )

    decoded_created_at, decoded_id = decode_and_verify_cursor(
        cursor_str=token,
        expected_org_id=org_id,
        expected_case_id=case_id,
        current_filters=filters,
        expected_sort=sort_order,
    )

    assert decoded_created_at == created_at
    assert decoded_id == row_id


def test_cursor_rejects_tampered_signature():
    org_id = "org-test-123"
    case_id = "case-abc-456"
    filters = {"status": "ACTIVE"}
    sort_order = "created_at_desc_id_desc"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id=case_id,
        current_filters=filters,
        sort_order=sort_order,
        created_at=created_at,
        row_id=row_id,
    )

    parts = token.split(".")
    tampered_sig = parts[1][:-4] + "ffff"
    tampered_token = f"{parts[0]}.{tampered_sig}"

    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=tampered_token,
            expected_org_id=org_id,
            expected_case_id=case_id,
            current_filters=filters,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "TAMPERED_CURSOR"


def test_cursor_rejects_cross_org_tampering():
    org_id = "org-attacker"
    case_id = "case-abc-456"
    filters = {"status": "ACTIVE"}
    sort_order = "created_at_desc_id_desc"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id=case_id,
        current_filters=filters,
        sort_order=sort_order,
        created_at=created_at,
        row_id=row_id,
    )

    # Attempt to decode within victim organization scope
    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=token,
            expected_org_id="org-victim",
            expected_case_id=case_id,
            current_filters=filters,
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "INVALID_CURSOR_SCOPE"


def test_cursor_rejects_cross_case_tampering():
    org_id = "org-test-123"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id="case-1",
        current_filters={},
        sort_order="created_at_desc_id_desc",
        created_at=created_at,
        row_id=row_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=token,
            expected_org_id=org_id,
            expected_case_id="case-2",
            current_filters={},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "INVALID_CURSOR_SCOPE"


def test_cursor_rejects_filter_mismatch():
    org_id = "org-test-123"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id=None,
        current_filters={"category": "CONFIDENTIAL"},
        sort_order="created_at_desc_id_desc",
        created_at=created_at,
        row_id=row_id,
    )

    # Caller changes filters
    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=token,
            expected_org_id=org_id,
            expected_case_id=None,
            current_filters={"category": "PUBLIC"},
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "CURSOR_FILTER_MISMATCH"


def test_cursor_rejects_sort_order_mismatch():
    org_id = "org-test-123"
    created_at = datetime(2026, 10, 30, 12, 0, 0, tzinfo=timezone.utc)
    row_id = uuid.uuid4()

    token = encode_cursor(
        organization_id=org_id,
        case_id=None,
        current_filters={},
        sort_order="created_at_desc_id_desc",
        created_at=created_at,
        row_id=row_id,
    )

    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=token,
            expected_org_id=org_id,
            expected_case_id=None,
            current_filters={},
            expected_sort="created_at_asc_id_asc",
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["code"] == "CURSOR_SORT_MISMATCH"


def test_cursor_requires_timezone_aware_timestamp():
    naive_dt = datetime(2026, 10, 30, 12, 0, 0)
    with pytest.raises(ValueError, match="timezone-aware"):
        encode_cursor(
            organization_id="org-1",
            case_id=None,
            current_filters={},
            sort_order="created_at_desc_id_desc",
            created_at=naive_dt,
            row_id=uuid.uuid4(),
        )


def test_cursor_rejects_non_url_safe_characters():
    # If a cursor contains '+' or '/'
    bad_token = "abc+def/123.sig"
    with pytest.raises(HTTPException) as exc_info:
        decode_and_verify_cursor(
            cursor_str=bad_token,
            expected_org_id="org-1",
            expected_case_id=None,
            current_filters={},
        )
    assert exc_info.value.status_code == 400
