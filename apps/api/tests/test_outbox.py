"""Outbox drain tests (M1-4)."""

from __future__ import annotations

import uuid

import httpx
import pytest

pytestmark = pytest.mark.integration

DEV_TENANT = uuid.UUID("11111111-1111-1111-1111-111111111111")


async def test_drain_returns_summary(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/v1/outbox/drain",
        headers={"X-Dev-Tenant-Id": str(DEV_TENANT)},
    )
    assert response.status_code == 200
    body = response.json()
    assert "claimed" in body
    assert "processed" in body
    assert "failed" in body
    assert "event_ids" in body