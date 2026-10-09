from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session to API route handlers.

    Guarantees the session is properly closed after request processing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
