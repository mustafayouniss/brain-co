import uuid
from datetime import datetime

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.session import engine
from app.models.user import User


def test_engine_hides_parameters():
    """Verify application database engine has hide_parameters enabled."""
    assert engine.hide_parameters is True


def test_create_user_success(db_session):
    """User is created with generated UUID, created_at timestamp, and is_active=True."""
    user = User(
        email="alice@example.com",
        full_name="Alice Smith",
        hashed_password="not-a-real-hash",
        role="admin",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert isinstance(user.created_at, datetime)
    assert user.is_active is True
    assert user.email == "alice@example.com"
    assert user.full_name == "Alice Smith"
    assert user.role == "admin"


def test_orm_lowercases_and_strips_email(db_session):
    """ORM model validator automatically normalizes email to lowercase and strips whitespace."""
    user = User(
        email="  Bob@Example.COM ",
        full_name="Bob Jones",
        hashed_password="not-a-real-hash",
        role="employee",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.email == "bob@example.com"


def test_duplicate_email_refused(db_session):
    """Inserting duplicate email fails with IntegrityError."""
    user1 = User(
        email="duplicate@example.com",
        full_name="User One",
        hashed_password="not-a-real-hash",
        role="employee",
    )
    db_session.add(user1)
    db_session.commit()

    user2 = User(
        email="duplicate@example.com",
        full_name="User Two",
        hashed_password="not-a-real-hash",
        role="employee",
    )
    db_session.add(user2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_duplicate_email_case_insensitive_refused(db_session):
    """Database unique index rejects case-insensitive email collision even when bypassing ORM validator."""
    user = User(
        email="carol@example.com",
        full_name="Carol White",
        hashed_password="not-a-real-hash",
        role="employee",
    )
    db_session.add(user)
    db_session.commit()

    # Raw SQL insert bypassing User model validator with different casing
    raw_insert = text(
        """
        INSERT INTO users (id, email, full_name, hashed_password, role, is_active, created_at)
        VALUES (gen_random_uuid(), 'Carol@Example.COM', 'Carol Duplicate', 'not-a-real-hash', 'employee', true, now())
        """
    )
    with pytest.raises(IntegrityError):
        db_session.execute(raw_insert)
        db_session.commit()
    db_session.rollback()


def test_invalid_role_refused(db_session):
    """Database check constraint rejects roles other than admin or employee."""
    user = User(
        email="hacker@example.com",
        full_name="Invalid Role User",
        hashed_password="not-a-real-hash",
        role="superuser",
    )
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_hashed_password_required(db_session):
    """Null hashed_password violates NOT NULL constraint and raises IntegrityError."""
    user = User(
        email="nopassword@example.com",
        full_name="No Password User",
        hashed_password=None,  # type: ignore[arg-type]
        role="employee",
    )
    db_session.add(user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
