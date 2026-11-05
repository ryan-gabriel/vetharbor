"""Integration tests for the M1 schema: RLS, vector dimensions, append-only.

These require a real Postgres (+ pgvector) at ``VETHARBOR_DATABASE_URL``
(default ``postgresql+psycopg://vetharbor:vetharbor@localhost:55432/vetharbor``).
They skip when no database is reachable so ``make test`` stays green on a
laptop without Docker; CI runs them against a real Postgres service.

All writes happen inside a rolled-back transaction so tests never leave data
behind. The application role ``vetharbor_app`` is used via ``SET ROLE`` so
row-level security is exercised for real (database superusers bypass RLS).
"""

from __future__ import annotations

import os
from uuid import uuid4

import psycopg
import pytest
from psycopg.errors import InsufficientPrivilege

from app.core.config import Settings

pytestmark = pytest.mark.integration

TENANT_TABLES = [
    "org_memberships",
    "job_roles",
    "documents",
    "document_chunks",
    "chunk_embeddings",
    "document_entities",
    "scores",
    "shadow_scores",
    "outbox_events",
    "dead_letter_events",
    "idempotency_keys",
    "rag_queries",
    "audit_log",
]

APP_ROLE = "vetharbor_app"


def database_url() -> str:
    return os.environ.get("VETHARBOR_DATABASE_URL") or Settings(
        _env_file=None
    ).database_url


@pytest.fixture(scope="session")
def pg_db() -> str:
    url = database_url()
    try:
        conn = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except Exception as exc:
        pytest.skip(f"no reachable Postgres at {url}: {exc}")
    conn.close()

    # Apply migrations head once for the session.
    from alembic import command
    from alembic.config import Config

    cfg = Config("apps/api/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    return url


@pytest.fixture
def db(pg_db: str):
    conn = psycopg.connect(pg_db)
    conn.autocommit = False
    try:
        yield conn
    finally:
        conn.rollback()
        conn.close()


def _set_tenant(cur, tenant_id: str) -> None:
    cur.execute(
        "SELECT set_config('vetharbor.tenant_id', %s, true)", (tenant_id,)
    )


def _insert_org_user_role_doc(cur, org_id, user_id, role_id, doc_id, model_id) -> None:
    conn = cur.connection
    conn.execute(
        "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, false)",
        (org_id, "org", "org"),
    )
    conn.execute(
        "INSERT INTO users (id, issuer, subject) VALUES (%s, 'https://x/', %s)",
        (user_id, str(user_id)[:8]),
    )
    conn.execute(
        "INSERT INTO job_roles (id, org_id, title, description, status) "
        "VALUES (%s, %s, %s, %s, 'open')",
        (role_id, org_id, "role", "desc"),
    )
    conn.execute(
        "INSERT INTO model_versions (id, name, version, algorithm, artifact_path, "
        "params, features, excluded_features, metrics, dataset_ref, "
        "model_card_path, is_active, is_shadow, trained_at) "
        "VALUES (%s, 'role_match', '1', 'logreg', 'p', '{}', '{}', '{}', "
        "'{}', 's', 'm', true, false, now())",
        (model_id,),
    )
    conn.execute(
        "INSERT INTO documents (id, org_id, kind, filename, declared_mime, "
        "detected_mime, sha256, size_bytes, page_count, extracted_text, "
        "char_count, word_count, status) "
        "VALUES (%s, %s, 'cv', 's.txt', 'text/plain', 'text/plain', %s, 1, 1, "
        "'doc', 3, 1, 'ready')",
        (doc_id, org_id, "0" * 64),
    )


def test_migration_head_applies(pg_db: str) -> None:
    """The fixture itself runs ``alembic upgrade head``; this asserts tables."""
    conn = psycopg.connect(pg_db)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            )
            assert cur.fetchone()[0] >= 15
    finally:
        conn.close()


def test_every_tenant_table_has_rls(pg_db: str) -> None:
    conn = psycopg.connect(pg_db)
    try:
        with conn.cursor() as cur:
            for table in TENANT_TABLES:
                cur.execute(
                    "SELECT relrowsecurity, relforcerowsecurity FROM pg_class "
                    "WHERE relname = %s", (table,)
                )
                row = cur.fetchone()
                assert row is not None, f"table {table} missing"
                assert row[0] is True, f"table {table} RLS not enabled"
                assert row[1] is True, f"table {table} RLS not forced"
    finally:
        conn.close()


def test_rls_policies_exist(pg_db: str) -> None:
    conn = psycopg.connect(pg_db)
    try:
        with conn.cursor() as cur:
            for table in TENANT_TABLES:
                cur.execute(
                    "SELECT count(*) FROM pg_policies WHERE tablename = %s",
                    (table,),
                )
                assert cur.fetchone()[0] >= 1, f"no policy for {table}"
    finally:
        conn.close()


def test_embedding_columns_are_768(pg_db: str) -> None:
    conn = psycopg.connect(pg_db)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT attrelid::regclass::text, attname "
                "FROM pg_attribute JOIN pg_type ON atttypid = oid "
                "WHERE typname = 'vector' AND atttypmod = 768"
            )
            found = {f"{table}.{attname}" for table, attname in cur.fetchall()}
    finally:
        conn.close()
    expected = {"chunk_embeddings.embedding", "job_roles.embedding"}
    assert expected.issubset(found), f"missing 768-d columns: {expected - found}"


def test_scores_append_only_for_app_role(db) -> None:
    org_id = uuid4()
    doc_id = uuid4()
    role_id = uuid4()
    model_id = uuid4()
    score_id = uuid4()
    with db.cursor() as cur:
        _insert_org_user_role_doc(cur, org_id, uuid4(), role_id, doc_id, model_id)
        cur.execute(
            "INSERT INTO scores (id, org_id, document_id, job_role_id, "
            "model_version_id, role_match_score, band, feature_skill_overlap, "
            "feature_years_experience, feature_embedding_similarity, evidence) "
            "VALUES (%s, %s, %s, %s, %s, 0.5, 'moderate', 0.5, 0.5, 0.5, '[]')",
            (score_id, org_id, doc_id, role_id, model_id),
        )
        cur.execute("SET ROLE vetharbor_app")
        # Update and delete are revoked for the application role.
        with pytest.raises(InsufficientPrivilege):
            cur.execute(
                "UPDATE scores SET role_match_score = 0.9 WHERE id = %s",
                (score_id,),
            )
        with pytest.raises(InsufficientPrivilege):
            cur.execute("DELETE FROM scores WHERE id = %s", (score_id,))
        # Insert still succeeds once tenant context is set (RLS WITH CHECK).
        cur.execute(
            "SELECT set_config('vetharbor.tenant_id', %s, true)", (str(org_id),)
        )
        cur.execute(
            "INSERT INTO scores (id, org_id, document_id, job_role_id, "
            "model_version_id, role_match_score, band, feature_skill_overlap, "
            "feature_years_experience, feature_embedding_similarity, evidence) "
            "VALUES (%s, %s, %s, %s, %s, 0.4, 'weak', 0.4, 0.4, 0.4, '[]')",
            (uuid4(), org_id, doc_id, role_id, model_id),
        )


def test_cross_tenant_read_returns_zero_rows(db) -> None:
    tenant_a = str(uuid4())
    tenant_b = str(uuid4())
    doc_a_id = uuid4()
    doc_b_id = uuid4()
    with db.cursor() as cur:
        # Superuser inserts under each tenant context (superuser bypasses RLS;
        # the session variables label whose data is whose).
        cur.execute(
            "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, false)",
            (tenant_a, "A", "a"),
        )
        cur.execute(
            "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, false)",
            (tenant_b, "B", "b"),
        )
        cur.execute(
            "INSERT INTO job_roles (id, org_id, title, description, status) "
            "VALUES (%s, %s, %s, %s, 'open')",
            (uuid4(), tenant_a, "Role A", "desc a"),
        )
        cur.execute(
            "INSERT INTO job_roles (id, org_id, title, description, status) "
            "VALUES (%s, %s, %s, %s, 'open')",
            (uuid4(), tenant_b, "Role B", "desc b"),
        )
        model_id = uuid4()
        cur.execute(
            "INSERT INTO model_versions (id, name, version, algorithm, artifact_path, "
            "params, features, excluded_features, metrics, dataset_ref, "
            "model_card_path, is_active, is_shadow, trained_at) "
            "VALUES (%s, 'role_match', '1', 'logreg', 'p', '{}', '{}', '{}', "
            "'{}', 's', 'm', true, false, now())",
            (model_id,),
        )
        _set_tenant(cur, tenant_a)
        cur.execute(
            "INSERT INTO documents (id, org_id, kind, filename, declared_mime, "
            "detected_mime, sha256, size_bytes, page_count, extracted_text, "
            "char_count, word_count, status) "
            "VALUES (%s, %s, 'cv', 'a.txt', 'text/plain', 'text/plain', %s, 1, 1, "
            "'doc a', 5, 1, 'ready')",
            (doc_a_id, tenant_a, "0" * 64),
        )
        _set_tenant(cur, tenant_b)
        cur.execute(
            "INSERT INTO documents (id, org_id, kind, filename, declared_mime, "
            "detected_mime, sha256, size_bytes, page_count, extracted_text, "
            "char_count, word_count, status) "
            "VALUES (%s, %s, 'cv', 'b.txt', 'text/plain', 'text/plain', %s, 1, 1, "
            "'doc b', 5, 1, 'ready')",
            (doc_b_id, tenant_b, "0" * 64),
        )

        # Application role under tenant A: tenant B's document must not exist.
        cur.execute("SET ROLE vetharbor_app")
        _set_tenant(cur, tenant_a)
        cur.execute("SELECT id FROM documents WHERE id = %s", (doc_b_id,))
        assert cur.fetchall() == []

        cur.execute("SELECT count(*) FROM documents WHERE id = %s", (doc_b_id,))
        assert cur.fetchone()[0] == 0

        cur.execute("SELECT count(*) FROM documents WHERE id = %s", (doc_a_id,))
        assert cur.fetchone()[0] == 1

        # The same holds when tenant B looks at tenant A's document.
        _set_tenant(cur, tenant_b)
        cur.execute("SELECT count(*) FROM documents WHERE id = %s", (doc_a_id,))
        assert cur.fetchone()[0] == 0


def test_tenant_setting_is_transaction_local(pg_db: str) -> None:
    """set_config(..., true) must not leak past transaction commit."""
    conn = psycopg.connect(pg_db)
    try:
        with conn.cursor() as cur:
            _set_tenant(cur, str(uuid4()))
            cur.execute("SELECT current_setting('vetharbor.tenant_id', true)")
            assert cur.fetchone()[0] is not None
        conn.commit()  # end transaction -> config resets
        with conn.cursor() as cur:
            cur.execute("SELECT current_setting('vetharbor.tenant_id', true)")
            assert cur.fetchone()[0] is None
    finally:
        conn.close()

