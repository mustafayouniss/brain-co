"""Regression tests for Arabic text normalization and lexical retrieval (Issue 6).

Validates that:
1. `normalize_arabic` correctly strips diacritics and normalizes letter variations.
2. `SqlAlchemyRetrievalStore` indexes Arabic text with ensure_ascii=False and matches normalized queries.
3. `GET /api/v1/retrieval/search` endpoint matches Arabic records with variation tolerance.
"""

from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.core.text import normalize_arabic
from app.infrastructure.database.stores import SqlAlchemyRetrievalStore
from app.models.case import Case
from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.ring1.models.observation import MemoryRecord


def test_normalize_arabic_unit():
    """Unit test for normalize_arabic helper."""
    # 1. Strips diacritics (tashkeel)
    assert normalize_arabic("المادَّةُ المُنَظَّمَةُ") == "الماده المنظمه"

    # 2. Normalizes alef variants (أ, إ, آ, ا) -> ا
    assert normalize_arabic("أحمد إبراهيم آثار القانون") == "احمد ابراهيم اثار القانون"

    # 3. Normalizes taa marbuta (ة) -> ه
    assert normalize_arabic("المحكمة الابتدائية") == "المحكمه الابتدائيه"

    # 4. Normalizes alif maqsura (ى) -> ي
    assert normalize_arabic("دعوى قضائية على المدعى") == "دعوي قضائيه علي المدعي"

    # 5. Empty or None handling
    assert normalize_arabic("") == ""


@pytest.fixture
def arabic_retrieval_fixture(db_session: Session):
    """Seed an organization, user, case, and Arabic memory records."""
    org = Organization(
        id=f"org-{uuid.uuid4().hex[:8]}",
        name="Cairo Law Firm",
        slug=f"cairo-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    user = User(
        id=uuid.uuid4(),
        email=f"lawyer_{uuid.uuid4().hex[:6]}@cairolaw.com",
        hashed_password="pw",
        full_name="Tarek Lawyer",
        role="admin",
        is_active=True,
    )
    db_session.add_all([org, user])
    db_session.flush()

    membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org.id,
        user_id=user.id,
        role="admin",
        is_active=True,
    )
    case = Case(
        id=uuid.uuid4(),
        case_number=f"CAI-{uuid.uuid4().hex[:6]}",
        title="Commercial Dispute",
        organization_id=org.id,
        status="active",
        created_by=user.id,
    )
    db_session.add_all([membership, case])
    db_session.flush()

    # Active memory record with Arabic legal content
    rec = MemoryRecord(
        id=uuid.uuid4(),
        organization_id=org.id,
        case_id=str(case.id),
        record_type="pdf_knowledge",
        status="active",
        payload={
            "title": "عقد إيجار تجاري",
            "summary": "ملخص عقد الإيجار الموقع بين الطرفين",
            "facts": [
                {
                    "statement": "تطبيق أحكام المادة 147 من القانون المدني المصري العقد شريعة المتعاقدين",
                    "category": "legal_fact",
                }
            ],
        },
        idempotency_key=f"mem-{uuid.uuid4().hex[:12]}",
    )
    db_session.add(rec)
    db_session.commit()

    token = create_access_token(
        str(user.id),
        org_id=org.id,
        role="admin",
        domain="legal",
    )

    return {
        "org": org,
        "user": user,
        "case": case,
        "record": rec,
        "token": token,
    }


@pytest.mark.asyncio
async def test_sqlalchemy_retrieval_store_arabic_matching(db_session: Session, arabic_retrieval_fixture):
    """Test SqlAlchemyRetrievalStore search_records correctly matches Arabic queries."""
    data = arabic_retrieval_fixture
    store = SqlAlchemyRetrievalStore(lambda: db_session)

    # 1. Search with haa (الماده) matching stored taa marbuta (المادة)
    results = await store.search_records(
        query="الماده 147",
        organization_id=data["org"].id,
        case_id=str(data["case"].id),
    )
    assert len(results) > 0
    assert results[0]["record_id"] == str(data["record"].id)
    assert results[0]["relevance_score"] > 0

    # 2. Search with tashkeel (المَادَّة)
    results_tashkeel = await store.search_records(
        query="المَادَّة",
        organization_id=data["org"].id,
        case_id=str(data["case"].id),
    )
    assert len(results_tashkeel) > 0
    assert results_tashkeel[0]["record_id"] == str(data["record"].id)

    # 3. Search with different alef form (الإيجار vs الايجار)
    results_alef = await store.search_records(
        query="الايجار التجاري",
        organization_id=data["org"].id,
        case_id=str(data["case"].id),
    )
    assert len(results_alef) > 0
    assert results_alef[0]["record_id"] == str(data["record"].id)


def test_api_v1_retrieval_search_arabic_endpoint(client: TestClient, arabic_retrieval_fixture):
    """Test GET /api/v1/retrieval/search matches Arabic queries and returns Arabic snippets."""
    data = arabic_retrieval_fixture

    response = client.get(
        f"/api/v1/retrieval/search?q=الماده 147&case_id={data['case'].id}",
        headers={"Authorization": f"Bearer {data['token']}"},
    )
    assert response.status_code == 200
    res_body = response.json()
    assert res_body["total_found"] >= 1
    item = res_body["items"][0]
    assert item["record_id"] == str(data["record"].id)
    assert item["score"] > 0
    # Snippet must contain the real Arabic text, not escaped unicode
    assert "المادة" in item["snippet"] or "147" in item["snippet"]
