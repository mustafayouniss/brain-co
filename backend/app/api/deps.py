from collections.abc import Generator
from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from app.db.session import SessionLocal

if TYPE_CHECKING:
    from ai.core.services.llm_service import LLMService


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a database session to API route handlers.

    Guarantees the session is properly closed after request processing.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@lru_cache()
def get_llm_service() -> "LLMService":
    """Dependency for providing the singleton configured LLMService instance.

    Higher rings and endpoint handlers inject this service via `Depends(get_llm_service)`.
    Can be overridden in tests via `app.dependency_overrides[get_llm_service] = ...`.
    """
    from ai.config.ai_config import ai_config

    return ai_config.create_service()

