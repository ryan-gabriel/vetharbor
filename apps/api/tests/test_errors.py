"""Error envelope is stable for domain and framework errors (TESTING.md §6)."""

from __future__ import annotations

import httpx
import pytest
from fastapi import FastAPI

from app.core.errors import ForbiddenError, ReadOnlyDemoError
from app.main import create_app

pytestmark = pytest.mark.unit


def _app_raising(exc: Exception) -> FastAPI:
    app = create_app()

    @app.get("/boom")
    async def boom() -> None:
        raise exc

    return app


async def test_domain_error_uses_envelope_and_code() -> None:
    transport = httpx.ASGITransport(app=_app_raising(ForbiddenError("no membership here")))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        response = await client.get("/boom", headers={"X-Request-ID": "corr-1"})
    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "no membership here",
            "correlation_id": "corr-1",
        }
    }


def test_read_only_demo_error_is_server_side() -> None:
    # SPEC.md F1: writes are refused with guidance, not a hidden button.
    assert ReadOnlyDemoError().status == 403
    assert "make dev" in ReadOnlyDemoError().message


async def test_unknown_route_returns_envelope_not_detail_shape(client) -> None:
    response = await client.get("/nope")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
