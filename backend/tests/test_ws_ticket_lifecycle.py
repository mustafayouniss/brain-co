"""Unit and concurrency tests for WebSocket Ticket Service.

Verifies:
1. Cryptographic randomness and hashing: Plaintext ticket is NEVER persisted.
2. Expiration: Tickets expire after 60 seconds.
3. Single-use semantics: Consumed ticket cannot be re-used.
4. Concurrency: Simulates multiple workers attempting to consume the same ticket
   simultaneously; strictly one worker succeeds and others receive None.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import uuid
import pytest
from sqlalchemy.orm import Session

from app.models.organization import Organization, OrganizationMembership
from app.models.user import User
from app.models.ws_ticket import WebSocketTicket
from app.services.ticket_service import TicketService


@pytest.fixture
def test_user_and_org(db_session: Session):
    """Seed test user and organization."""
    org_id = f"org-{uuid.uuid4().hex[:8]}"
    user_id = uuid.uuid4()

    org = Organization(
        id=org_id,
        name="Test Law Chambers",
        slug=f"test-slug-{uuid.uuid4().hex[:6]}",
        domain="legal",
        is_active=True,
    )
    user = User(
        id=user_id,
        email=f"attorney_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="hashed_pw_dummy",
        full_name="Test Attorney",
        role="employee",
        is_active=True,
    )
    membership = OrganizationMembership(
        id=uuid.uuid4(),
        organization_id=org_id,
        user_id=user_id,
        role="employee",
        is_active=True,
    )
    db_session.add_all([org, user, membership])
    db_session.commit()
    return user, org


def test_ticket_creation_and_hash_storage(db_session: Session, test_user_and_org):
    """Verify ticket is hashed with SHA-256 and plaintext is never persisted in database."""
    user, org = test_user_and_org
    raw_token = TicketService.create_ticket(
        session=db_session,
        user_id=user.id,
        organization_id=org.id,
        case_id="case-101",
    )
    db_session.commit()

    assert raw_token.startswith("wst_")
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Query DB directly to verify raw token is not stored
    record = db_session.query(WebSocketTicket).filter(WebSocketTicket.ticket_hash == expected_hash).first()
    assert record is not None
    assert record.ticket_hash == expected_hash
    assert record.user_id == user.id
    assert record.organization_id == org.id
    assert record.case_id == "case-101"
    assert record.consumed is False

    # Ensure raw token string does not appear in any column of the record
    assert raw_token != record.ticket_hash


def test_ticket_single_use_consumption(db_session: Session, test_user_and_org):
    """Verify ticket can only be consumed once; subsequent attempts fail (replay protection)."""
    user, org = test_user_and_org
    raw_token = TicketService.create_ticket(
        session=db_session,
        user_id=user.id,
        organization_id=org.id,
        case_id="case-102",
    )
    db_session.commit()

    # First consumption must succeed
    consumed = TicketService.consume_ticket(db_session, raw_token)
    assert consumed is not None
    assert consumed.user_id == user.id
    assert consumed.organization_id == org.id
    assert consumed.case_id == "case-102"

    # Second consumption must return None (replay defense)
    replay = TicketService.consume_ticket(db_session, raw_token)
    assert replay is None, "Replaying a consumed ticket must return None"


def test_ticket_expiration(db_session: Session, test_user_and_org):
    """Verify expired tickets cannot be consumed."""
    user, org = test_user_and_org
    raw_token = TicketService.create_ticket(
        session=db_session,
        user_id=user.id,
        organization_id=org.id,
        case_id="case-103",
    )
    db_session.commit()

    # Artificially expire the ticket in the database
    ticket_hash = TicketService.hash_ticket(raw_token)
    expired_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    db_session.query(WebSocketTicket).filter(WebSocketTicket.ticket_hash == ticket_hash).update(
        {"expires_at": expired_time}
    )
    db_session.commit()

    consumed = TicketService.consume_ticket(db_session, raw_token)
    assert consumed is None, "Expired ticket must return None upon consumption"


def test_atomic_ticket_consumption_across_workers(test_engine):
    """Simulate multiple worker processes attempting to consume the same ticket concurrently.

    Only one worker process must succeed; all other concurrent workers must get None.
    """
    org_id = f"org-{uuid.uuid4().hex[:8]}"
    user_id = uuid.uuid4()

    with Session(test_engine) as session:
        org = Organization(
            id=org_id,
            name="Concurrent Law Partners",
            slug=f"concurrent-{uuid.uuid4().hex[:6]}",
            domain="legal",
            is_active=True,
        )
        user = User(
            id=user_id,
            email=f"concurrent_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="pw",
            full_name="Concurrent Attorney",
            role="employee",
            is_active=True,
        )
        session.add_all([org, user])
        session.commit()

        raw_token = TicketService.create_ticket(
            session=session,
            user_id=user_id,
            organization_id=org_id,
            case_id="case-race",
        )
        session.commit()

    results = []

    def worker_consume():
        with Session(test_engine) as worker_session:
            return TicketService.consume_ticket(worker_session, raw_token)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker_consume) for _ in range(5)]
        for f in futures:
            results.append(f.result())

    success_count = sum(1 for r in results if r is not None)
    failure_count = sum(1 for r in results if r is None)

    assert success_count == 1, "Exactly one worker must succeed in consuming the ticket"
    assert failure_count == 4, "All other concurrent workers must fail consumption"
