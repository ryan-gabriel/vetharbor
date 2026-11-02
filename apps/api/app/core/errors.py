"""Typed domain errors mapped to the client error union.

The union is fixed by ARCHITECTURE.md §11: every HTTP failure an agent or the
SPA sees is one of these codes. A raw ``ProgrammingError`` must never reach a
client (AGENTS.md §8).
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorCode(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    WAKING_UP = "waking_up"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    READ_ONLY = "read_only"
    SERVER = "server"


class AppError(Exception):
    """Base for domain errors. Carries its HTTP status and a safe message.

    Subclasses override ``message`` as a class attribute; passing a message
    to the constructor overrides it per instance.
    """

    code: ErrorCode = ErrorCode.SERVER
    status: int = 500
    message: str = "The request could not be completed."

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class UnauthenticatedError(AppError):
    code = ErrorCode.UNAUTHENTICATED
    status = 401


class WakingUpError(AppError):
    code = ErrorCode.WAKING_UP
    status = 503


class ForbiddenError(AppError):
    code = ErrorCode.FORBIDDEN
    status = 403


class NotFoundError(AppError):
    code = ErrorCode.NOT_FOUND
    status = 404


class RateLimitedError(AppError):
    code = ErrorCode.RATE_LIMITED
    status = 429


class ReadOnlyDemoError(AppError):
    """The public demo is read-only server-side (SPEC.md F1; ADR-010)."""

    code = ErrorCode.READ_ONLY
    status = 403
    message = (
        "This demo tenant is read-only. Upload is demonstrated by `make dev` "
        "and in the recorded walkthrough."
    )


def error_envelope(code: ErrorCode, message: str, correlation_id: str | None) -> dict[str, Any]:
    return {"error": {"code": code.value, "message": message, "correlation_id": correlation_id}}


_STATUS_TO_CODE: dict[int, ErrorCode] = {
    401: ErrorCode.UNAUTHENTICATED,
    403: ErrorCode.FORBIDDEN,
    404: ErrorCode.NOT_FOUND,
    429: ErrorCode.RATE_LIMITED,
    503: ErrorCode.WAKING_UP,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=exc.status,
            content=error_envelope(exc.code, exc.message, correlation_id),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Framework errors (404 routing, 422 validation) use the same envelope."""
        correlation_id = getattr(request.state, "correlation_id", None)
        code = _STATUS_TO_CODE.get(exc.status_code, ErrorCode.SERVER)
        message = str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_envelope(code, message, correlation_id),
        )
