"""Shared fixtures. CI runs the app with fake providers and no database
(TESTING.md §1): engines are lazy, so nothing here opens a connection."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.main import create_app


@pytest.fixture
def settings() -> Settings:
    return Settings(_env_file=None, environment="test")


@pytest.fixture
def app(settings: Settings):  # type: ignore[no-untyped-def]
    return create_app(settings)


@pytest.fixture
async def client(app) -> httpx.AsyncClient:  # type: ignore[no-untyped-def]
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
