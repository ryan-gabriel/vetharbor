"""Tenant resolution rules (ADR-006; AGENTS.md §3.9).

The M1 placeholder resolves a fixed dev tenant. The one thing that must never
leak into a deployment is trusting ``X-Dev-Tenant-Id`` from a caller.
"""

from __future__ import annotations

import uuid

import httpx
import pytest

from app.core.auth import DEV_TENANT_ID, dev_header_allowed, resolve_tenant_from
from app.core.config import Settings

pytestmark = pytest.mark.unit

OTHER = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


@pytest.mark.parametrize("environment", ["dev", "test"])
def test_dev_header_is_honoured_outside_prod(environment: str) -> None:
    ctx = resolve_tenant_from(Settings(_env_file=None, environment=environment), str(OTHER))  # type: ignore[arg-type]
    assert ctx.tenant_id == OTHER


def test_dev_header_is_ignored_in_prod() -> None:
    # A deployed demo must not let a caller choose org B (AGENTS.md §3.9).
    ctx = resolve_tenant_from(Settings(_env_file=None, environment="prod"), str(OTHER))
    assert ctx.tenant_id == DEV_TENANT_ID


def test_malformed_dev_header_falls_back_to_the_dev_tenant() -> None:
    ctx = resolve_tenant_from(Settings(_env_file=None), "not-a-uuid")
    assert ctx.tenant_id == DEV_TENANT_ID


def test_dev_header_allowed_matrix() -> None:
    assert dev_header_allowed("dev") is True
    assert dev_header_allowed("test") is True
    assert dev_header_allowed("prod") is False


async def test_prod_app_ignores_the_dev_tenant_header(client_factory) -> None:  # type: ignore[no-untyped-def]
    # End-to-end: the header is present in the request but the response is the
    # dev tenant's data, so a public deployment cannot be steered by a client.
    client: httpx.AsyncClient = await client_factory(environment="prod")
    async with client:
        response = await client.get("/api/v1/documents", headers={"X-Dev-Tenant-Id": str(OTHER)})
    assert response.status_code == 200
    for item in response.json()["items"]:
        assert item["org_id"] == str(DEV_TENANT_ID)
