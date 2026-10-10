import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)

HTTP_STATUS_CODE_MAP: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "BAD_REQUEST",
    status.HTTP_401_UNAUTHORIZED: "UNAUTHORIZED",
    status.HTTP_403_FORBIDDEN: "FORBIDDEN",
    status.HTTP_404_NOT_FOUND: "NOT_FOUND",
    status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
    status.HTTP_408_REQUEST_TIMEOUT: "REQUEST_TIMEOUT",
    status.HTTP_409_CONFLICT: "CONFLICT",
    status.HTTP_422_UNPROCESSABLE_CONTENT: "UNPROCESSABLE_ENTITY",
    status.HTTP_429_TOO_MANY_REQUESTS: "TOO_MANY_REQUESTS",
    status.HTTP_500_INTERNAL_SERVER_ERROR: "INTERNAL_SERVER_ERROR",
    status.HTTP_502_BAD_GATEWAY: "BAD_GATEWAY",
    status.HTTP_503_SERVICE_UNAVAILABLE: "SERVICE_UNAVAILABLE",
    status.HTTP_504_GATEWAY_TIMEOUT: "GATEWAY_TIMEOUT",
}


def register_exception_handlers(app: FastAPI) -> None:
    """Register standard error handlers on the provided FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = HTTP_STATUS_CODE_MAP.get(exc.status_code, f"HTTP_{exc.status_code}")
        if isinstance(exc.detail, str):
            message = exc.detail
            details: Any = None
        else:
            message = "An HTTP error occurred"
            details = exc.detail

        error_content: dict[str, Any] = {
            "code": code,
            "message": message,
        }
        if details is not None:
            error_content["details"] = details

        return JSONResponse(
            status_code=exc.status_code,
            content={"error": error_content},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = [
            {
                "field": ".".join(str(p) for p in err.get("loc", [])),
                "message": err.get("msg", ""),
                "type": err.get("type", ""),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": details,
                }
            },
        )

<<<<<<< HEAD
=======
    try:
        from ai.core.types.error import LLMError, LLMErrorType

        llm_status_map = {
            LLMErrorType.AUTHENTICATION_FAILED: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.RATE_LIMITED: status.HTTP_429_TOO_MANY_REQUESTS,
            LLMErrorType.MODEL_UNAVAILABLE: status.HTTP_503_SERVICE_UNAVAILABLE,
            LLMErrorType.INVALID_REQUEST: status.HTTP_400_BAD_REQUEST,
            LLMErrorType.TIMEOUT: status.HTTP_504_GATEWAY_TIMEOUT,
            LLMErrorType.PROVIDER_ERROR: status.HTTP_502_BAD_GATEWAY,
            LLMErrorType.UNKNOWN: status.HTTP_500_INTERNAL_SERVER_ERROR,
        }

        @app.exception_handler(LLMError)
        async def llm_exception_handler(
            request: Request, exc: LLMError
        ) -> JSONResponse:
            logger.error("LLM Provider Exception [%s]: %s", exc.provider_id, exc.message)
            status_code = llm_status_map.get(
                exc.error_type, status.HTTP_502_BAD_GATEWAY
            )
            details = {"provider": exc.provider_id} if exc.provider_id else None
            error_data = {
                "code": f"AI_{exc.error_type.value}",
                "message": exc.message,
            }
            if details is not None:
                error_data["details"] = details

            return JSONResponse(
                status_code=status_code,
                content={"error": error_data},
            )
    except ImportError:
        pass

>>>>>>> origin/main
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "Internal server error",
                }
            },
        )
