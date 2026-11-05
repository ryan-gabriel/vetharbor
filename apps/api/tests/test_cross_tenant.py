"""Cross-tenant isolation at the API level (M1-5, F7).

Proves that tenant A cannot read tenant B's documents through the API,
and that the database returns zero rows under RLS. Uses two dev tenants
seeded into the test database.
"""

from __future__ import annotations

import uuid

import httpx
import pytest

pytestmark = pytest.mark.integration

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
DEV_USER = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture(autouse=True)
async def seed_two_tenants() -> None:
    import psycopg

    db_url = "postgresql://vetharbor:vetharbor@localhost:55432/vetharbor"
    try:
        conn = psycopg.connect(db_url, autocommit=True)
    except Exception:
        pytest.skip("no reachable Postgres")
    # Clean slate.
    conn.execute("DELETE FROM documents WHERE org_id IN (%s, %s)", (TENANT_A, TENANT_B))
    conn.execute("DELETE FROM org_memberships WHERE org_id IN (%s, %s)", (TENANT_A, TENANT_B))
    conn.execute("DELETE FROM orgs WHERE id IN (%s, %s)", (TENANT_A, TENANT_B))
    # Create tenants.
    conn.execute(
        "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, true)",
        (TENANT_A, "Tenant A", "tenant-a"),
    )
    conn.execute(
        "INSERT INTO orgs (id, name, slug, is_demo) VALUES (%s, %s, %s, true)",
        (TENANT_B, "Tenant B", "tenant-b"),
    )
    # Ensure dev user exists.
    conn.execute(
        "INSERT INTO users (id, issuer, subject, display_name) "
        "VALUES (%s, 'https://dev/', %s, 'Dev User') ON CONFLICT (id) DO NOTHING",
        (DEV_USER, str(DEV_USER)[:8]),
    )
    # Memberships.
    conn.execute(
        "INSERT INTO org_memberships (id, org_id, user_id, role, status) "
        "VALUES (gen_random_uuid(), %s, %s, 'admin', 'active')",
        (TENANT_A, DEV_USER),
    )
    conn.execute(
        "INSERT INTO org_memberships (id, org_id, user_id, role, status) "
        "VALUES (gen_random_uuid(), %s, %s, 'admin', 'active')",
        (TENANT_B, DEV_USER),
    )
    # Insert a document under tenant B (as superuser, bypassing RLS).
    doc_b_id = uuid.uuid4()
    conn.execute(
        "INSERT INTO documents (id, org_id, kind, filename, declared_mime, "
        "detected_mime, sha256, size_bytes, page_count, extracted_text, "
        "char_count, word_count, status) "
        "VALUES (%s, %s, 'cv', 'secret.txt', 'text/plain', 'text/plain', %s, 1, 1, "
        "'secret doc b', 10, 2, 'ready')",
        (doc_b_id, TENANT_B, "0" * 64),
    )
    conn.close()
    # Store doc_b_id for tests.
    pytest.doc_b_id = doc_b_id  # type: ignore[attr-defined]


async def test_cross_tenant_get_returns_not_found(client: httpx.AsyncClient) -> None:
    """Tenant A requesting tenant B's document gets 404, not the document."""
    doc_b_id = pytest.doc_b_id  # type: ignore[attr-defined]
    # Act as tenant A.
    response = await client.get(
        f"/api/v1/documents/{doc_b_id}",
        headers={"X-Dev-Tenant-Id": str(TENANT_A)},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


async def test_cross_tenant_list_excludes_other_tenant(client: httpx.AsyncClient) -> None:
    """Tenant A's document list does not include tenant B's documents."""
    response = await client.get(
        "/api/v1/documents",
        headers={"X-Dev-Tenant-Id": str(TENANT_A)},
    )
    assert response.status_code == 200
    body = response.json()
    for item in body["items"]:
        assert item["org_id"] == str(TENANT_A)


async def test_cross_tenant_direct_sql_zero_rows() -> None:
    """Direct SQL under tenant A's RLS context returns zero rows for tenant B's doc."""
    import psycopg

    db_url = "postgresql://vetharbor:vetharbor@localhost:55432/vetharbor"
    doc_b_id = pytest.doc_b_id  # type: ignore[attr-defined]
    conn = psycopg.connect(db_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SET ROLE vetharbor_app")
            cur.execute(
                "SELECT set_config('vetharbor.tenant_id', %s, true)",
                (str(TENANT_A),),
            )
            cur.execute("SELECT count(*) FROM documents WHERE id = %s", (doc_b_id,))
            assert cur.fetchone()[0] == 0
    finally:
        conn.close()


async def test_tenant_switch_cannot_select_unowned_org(client: httpx.AsyncClient) -> None:
    """A caller cannot select an org they don't belong to."""
    # Tenant C doesn't exist — should still return empty list, not error.
    tenant_c = uuid.uuid4()
    response = await client.get(
        "/api/v1/documents",
        headers={"X-Dev-Tenant-Id": str(tenant_c)},
    )
    # Should succeed (empty list) since RLS returns zero rows, not 403.
    assert response.status_code == 200
    assert response.json()["total"] == 0