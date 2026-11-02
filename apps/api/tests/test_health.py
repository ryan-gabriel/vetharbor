"""Health route + correlation contract (ARCHITECTURE.md §13)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


async def test_healthz_returns_ok_with_profile(client) -> None:
    response = await client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["profile"] == "dev"


async def test_healthz_generates_correlation_id(client) -> None:
    response = await client.get("/healthz")
    assert len(response.headers["x-request-id"]) == 32


async def test_healthz_echoes_valid_inbound_correlation_id(client) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": "abc-123"})
    assert response.headers["x-request-id"] == "abc-123"


async def test_correlation_id_rejects_non_printable_inbound(client) -> None:
    spoofed = "bad\r\nid"
    response = await client.get("/healthz", headers={"X-Request-ID": spoofed})
    assert response.headers["x-request-id"] != spoofed
