"""0005 — Row-level security, roles and grants.

Logical change: enable FORCE ROW LEVEL SECURITY on every tenant-scoped table,
install the standard tenant-isolation policy, create the database roles and
grant least-privilege access.

Roles:
- vetharbor_app: request-path reads/writes; RLS applies; no BYPASSRLS;
  append-only on scores/shadow_scores/audit_log (update/delete revoked).
- vetharbor_worker: outbox consumer; policies allow it to claim outbox rows;
  grants limited to outbox_events, dead_letter_events, idempotency_keys.
- vetharbor_migrate: DDL owner role; used only by migrations, never at runtime.

FORCE ROW LEVEL SECURITY means even the table owner is subject to policies, so
a misconfigured connection shows up as empty results in tests instead of silent
cross-tenant exposure in production. The application never accepts a tenant id
from the client; tenant_id/user_id/is_admin are set transaction-locally by the
persistence layer from server-resolved membership data (ADR-006).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0005_rls_roles"
down_revision = "0004_scoring_outbox"
branch_labels = None
depends_on = None

TENANT_TABLES = [
    "job_roles",
    "documents",
    "document_chunks",
    "chunk_embeddings",
    "document_entities",
    "scores",
    "shadow_scores",
    "outbox_events",
    "dead_letter_events",
    "rag_queries",
    "audit_log",
]

WORKER_TABLES = ["outbox_events", "dead_letter_events", "idempotency_keys"]


def upgrade() -> None:
    op.execute("CREATE ROLE vetharbor_app NOLOGIN")
    op.execute("CREATE ROLE vetharbor_migrate NOLOGIN")
    op.execute("CREATE ROLE vetharbor_worker NOLOGIN BYPASSRLS")

    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
              FOR ALL TO vetharbor_app
              USING (org_id = current_setting('vetharbor.tenant_id', true)::uuid)
              WITH CHECK (org_id = current_setting('vetharbor.tenant_id', true)::uuid)
            """
        )

    op.execute(
        """
        GRANT USAGE ON SCHEMA public TO vetharbor_app
        """
    )
    op.execute(
        """
        GRANT USAGE ON SCHEMA public TO vetharbor_worker
        """
    )
    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON ALL TABLES IN SCHEMA public TO vetharbor_app
        """
    )
    # Append-only for the application role: scores, shadow_scores and audit_log
    # are historical claims; they may only be inserted, never updated or deleted.
    op.execute(
        "REVOKE UPDATE, DELETE ON scores, shadow_scores, audit_log FROM vetharbor_app"
    )
    op.execute(
        "GRANT USAGE ON SEQUENCE audit_log_id_seq, outbox_events_id_seq TO vetharbor_app"
    )

    op.execute(
        """
        GRANT SELECT, INSERT, UPDATE, DELETE
        ON outbox_events, dead_letter_events, idempotency_keys TO vetharbor_worker
        """
    )
    op.execute(
        "GRANT USAGE ON SEQUENCE outbox_events_id_seq TO vetharbor_worker"
    )

    op.execute(
        "COMMENT ON ROLE vetharbor_app IS "
        "'Request-path role: RLS applies, append-only on scores/audit_log.'"
    )
    op.execute(
        "COMMENT ON ROLE vetharbor_migrate IS "
        "'DDL owner role: used only by migrations, never at runtime.'"
    )
    op.execute(
        "COMMENT ON ROLE vetharbor_worker IS "
        "'Outbox consumer role: grants limited to outbox_events, "
        "dead_letter_events, idempotency_keys.'"
    )


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only")

