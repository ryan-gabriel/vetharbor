"""Shared fixtures. CI runs the app with fake providers and no database
(TESTING.md §1): engines are lazy, so nothing here opens a connection."""

from __future__ import annotations

import asyncio
import platform
import uuid

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app

# Psycopg async requires SelectorEventLoop on Windows (ProactorEventLoop is
# incompatible). CI runs on Linux where this is a no-op.
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

DEV_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEV_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, environment="test")


@pytest.fixture
def app(settings: Settings):  # type: ignore[no-untyped-def]
    return create_app(settings)


@pytest.fixture
async def client(app) -> httpx.AsyncClient:  # type: ignore[no-untyped-def]
    # Ensure the dev tenant and user exist in the database.
    import psycopg

    db_url = "postgresql://vetharbor:vetharbor@localhost:55432/vetharbor"
    try:
        conn = psycopg.connect(db_url, autocommit=True)
        conn.execute(
            "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, true) "
            "ON CONFLICT (id) DO NOTHING",
            (DEV_TENANT_ID, "Harbor Recruiting", "harbor"),
        )
        conn.execute(
            "INSERT INTO users (id, issuer, subject, display_name) "
            "VALUES (%s, 'https://dev/', %s, 'Dev User') ON CONFLICT (id) DO NOTHING",
            (DEV_USER_ID, str(DEV_USER_ID)[:8]),
        )
        conn.execute(
            "INSERT INTO org_memberships (id, org_id, user_id, role, status) "
            "VALUES (gen_random_uuid(), %s, %s, 'admin', 'active') "
            "ON CONFLICT (org_id, user_id) DO NOTHING",
            (DEV_TENANT_ID, DEV_USER_ID),
        )
        # Clean up documents from previous test runs.
        conn.execute(
            "DELETE FROM documents WHERE org_id = %s", (DEV_TENANT_ID,)
        )
        conn.close()
    except Exception:
        pass
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
