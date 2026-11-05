"""0001 — PostgreSQL extensions and enum types.

Logical change: install the citext and pgvector extensions and create every
Postgres enum type used by the M1 schema.

Extensions are required before any column cites them (citext for
users.email, vector for every embedding column). Enums are created before
tables so column definitions can reference them.

This migration is forward-only: there is no safe automatic reverse for
dropping shared extensions or enum types.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_postgres_extensions_and_enums"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute(
        "CREATE TYPE user_role AS ENUM ('admin', 'recruiter', 'demo_reader')"
    )
    op.execute(
        "CREATE TYPE membership_status AS ENUM ('invited', 'active', 'revoked')"
    )
    op.execute(
        "CREATE TYPE document_kind AS ENUM ('cv', 'proposal', 'paper')"
    )
    op.execute(
        "CREATE TYPE document_status AS ENUM "
        "('pending', 'processing', 'ready', 'failed', 'rejected')"
    )
    op.execute(
        "CREATE TYPE entity_source AS ENUM ('ner', 'rule', 'regex', 'gazetteer')"
    )
    op.execute(
        "CREATE TYPE job_role_status AS ENUM ('draft', 'open', 'closed')"
    )
    op.execute(
        "CREATE TYPE score_band AS ENUM "
        "('strong', 'moderate', 'weak', 'insufficient_evidence')"
    )
    op.execute(
        "CREATE TYPE event_type AS ENUM "
        "('document.uploaded', 'document.re_extract_requested', "
        "'job_role.embed_requested')"
    )
    op.execute(
        "CREATE TYPE outbox_status AS ENUM ('pending', 'claimed', 'done', 'failed')"
    )
    op.execute(
        "CREATE TYPE rag_outcome AS ENUM "
        "('answered', 'refused_no_evidence', 'blocked_injection', 'error')"
    )
    op.execute(
        "CREATE TYPE audit_result AS ENUM ('success', 'denied', 'failed')"
    )


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only")

