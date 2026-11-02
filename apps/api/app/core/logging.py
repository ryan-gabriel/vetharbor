"""Request logging and correlation.

One JSON line per request (AGENTS.md §8). Never log document text, questions,
answers, emails or names - the fields below are request metadata only.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime

from starlette.requests import Request
from starlette.types import ASGIApp, Message, Receive, Scope, Send

CORRELATION_HEADER = "X-Request-ID"

logger = logging.getLogger("vetharbor.access")


def _printable_ascii(value: str) -> bool:
    return all(32 <= ord(c) < 127 for c in value)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


class CorrelationMiddleware:
    """Pure-ASGI middleware: resolve the correlation id, stamp the response,
    and emit exactly one JSON log line per request (ARCHITECTURE.md §13)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        correlation_id = _correlation_id(request)
        request.state.correlation_id = correlation_id
        start = time.perf_counter()
        status_holder = {"status": 0}

        async def send_with_header(message: Message) -> None:
            if message["type"] == "http.response.start":
                status_holder["status"] = int(message["status"])
                headers = list(message.get("headers") or [])
                headers.append((b"x-request-id", correlation_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        finally:
            entry = {
                "ts": _now_iso(),
                "level": "INFO",
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status": status_holder["status"],
                "duration_ms": round((time.perf_counter() - start) * 1000, 1),
            }
            logger.info(json.dumps(entry, separators=(",", ":")))


def _correlation_id(request: Request) -> str:
    inbound = request.headers.get(CORRELATION_HEADER)
    if inbound and len(inbound) <= 64 and _printable_ascii(inbound):
        return inbound
    return uuid.uuid4().hex
