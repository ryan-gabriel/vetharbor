"""RLS context helpers must stay transaction-local; engine stays lazy
(DATA_MODEL.md §4.1, §4.4.5). No connection is opened here (TESTING.md §1)."""

from __future__ import annotations

import pytest

from app.core.config import Settings
from app.persistence.db import (
    SET_ADMIN_SQL,
    SET_TENANT_SQL,
    SET_USER_SQL,
    Database,
    create_engine,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize("stmt", [SET_TENANT_SQL, SET_USER_SQL, SET_ADMIN_SQL])
def test_set_config_is_transaction_local(stmt) -> None:
    sql = str(stmt.compile())
    assert "set_config(" in sql
    assert sql.rstrip().endswith("true)")


def test_engine_dialect_is_psycopg3_without_connecting() -> None:
    engine = create_engine(Settings(_env_file=None))
    assert engine.url.get_backend_name() == "postgresql"
    assert engine.url.get_driver_name() == "psycopg"


def test_database_holder_creates_engine_and_factory_once() -> None:
    db = Database(Settings(_env_file=None))
    assert db._engine is None
    engine = db.engine
    assert db.engine is engine
    assert db.session_factory is db.session_factory
