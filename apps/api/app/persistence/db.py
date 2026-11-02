"""Async engine and the RLS session-context helpers (DATA_MODEL.md §4)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import Settings


class Base(DeclarativeBase):
    """Declarative base; models arrive with the first M1 migration."""


def create_engine(settings: Settings) -> AsyncEngine:
    """Create the engine. No connection is opened until first use, so unit
    tests never require a database (TESTING.md §1: determinism over realism)."""
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


# Transaction-local (third argument TRUE) so a pooled connection can never
# leak one tenant's settings into another request (DATA_MODEL.md §4.1, §4.4.5).
SET_TENANT_SQL = text("SELECT set_config('vetharbor.tenant_id', :tenant_id, true)")
SET_USER_SQL = text("SELECT set_config('vetharbor.user_id', :user_id, true)")
SET_ADMIN_SQL = text("SELECT set_config('vetharbor.is_admin', :is_admin, true)")


async def set_tenant_context(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    is_admin: bool,
) -> None:
    """Set the RLS variables for the current transaction.

    ``tenant_id`` must be the server-resolved value from ``org_memberships``
    (ADR-006); the client never supplies it.
    """
    await session.execute(SET_TENANT_SQL, {"tenant_id": str(tenant_id)})
    await session.execute(SET_USER_SQL, {"user_id": str(user_id) if user_id else ""})
    await session.execute(SET_ADMIN_SQL, {"is_admin": "on" if is_admin else "off"})


class Database:
    """Small holder wired onto ``app.state``; owns lazy engine + factory."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine: AsyncEngine | None = None
        self._factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_engine(self._settings)
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._factory is None:
            self._factory = make_session_factory(self.engine)
        return self._factory

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._factory = None

    @asynccontextmanager
    async def tenant_session(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID | None,
        is_admin: bool,
    ) -> AsyncIterator[AsyncSession]:
        """One transaction with RLS context applied before any statement."""
        async with self.session_factory() as session, session.begin():
            await set_tenant_context(
                session, tenant_id=tenant_id, user_id=user_id, is_admin=is_admin
            )
            yield session
