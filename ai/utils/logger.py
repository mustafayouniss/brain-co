import json
import logging
from typing import Any, Protocol


class ILogger(Protocol):
    """Protocol for loggers consumed by LLMService."""

    def info(self, data: dict[str, Any]) -> None: ...
    def error(self, data: dict[str, Any]) -> None: ...
    def warning(self, data: dict[str, Any]) -> None: ...


class AILogger:
    """Structured JSON logger using standard Python logging."""

    def __init__(self, name: str = "orgbrain.ai"):
        self.logger = logging.getLogger(name)

    def info(self, data: dict[str, Any]) -> None:
        self.logger.info(json.dumps(data, ensure_ascii=False))

    def error(self, data: dict[str, Any]) -> None:
        self.logger.error(json.dumps(data, ensure_ascii=False))

    def warning(self, data: dict[str, Any]) -> None:
        self.logger.warning(json.dumps(data, ensure_ascii=False))


def get_ai_logger(name: str = "orgbrain.ai") -> AILogger:
    """Return default AI logger instance."""
    return AILogger(name)
