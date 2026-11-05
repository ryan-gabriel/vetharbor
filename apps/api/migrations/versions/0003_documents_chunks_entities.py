"""0003 — Document, chunk, embedding and entity tables.

Logical change: create documents, document_chunks, chunk_embeddings and
document_entities with their foreign keys, indexes and the pgvector HNSW
index.

chunk_embeddings.embedding is vector(768) NOT NULL and dimensions carries a
check constraint (dimensions = 768) as a tripwire; the real guard is the
repository-side dimension assertion before any write.

Postgres GIN has no built-in opclass for composite int/text keys, so the
DATA_MODEL.md §3.8 "GIN on (org_id, label, normalised)" intent is implemented
as a b-tree on (org_id, label) plus a pg_trgm GIN on normalised — equivalent
lookup semantics for organisation + label filtering and normalised-value
searches.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_documents_chunks_entities"
down_revision = "0002_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.execute(
        """
        CREATE TABLE documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL REFERENCES orgs ON DELETE CASCADE,
            kind document_kind NOT NULL,
            filename text NOT NULL,
            declared_mime text NOT NULL,
            detected_mime text NOT NULL,
            sha256 char(64) NOT NULL,
            size_bytes bigint NOT NULL
                CHECK (size_bytes > 0 AND size_bytes <= 5242880),
            page_count int CHECK (page_count BETWEEN 1 AND 60),
            extracted_text text NOT NULL,
            char_count int NOT NULL,
            word_count int NOT NULL,
            language text NOT NULL DEFAULT 'en',
            status document_status NOT NULL DEFAULT 'pending',
            warning_flags text[] NOT NULL DEFAULT '{}',
            uploaded_by uuid REFERENCES users,
            failure_reason text,
            created_at timestamptz,
            updated_at timestamptz,
            deleted_at timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_documents_org_status ON documents (org_id, status)"
    )
    op.execute(
        "CREATE INDEX ix_documents_org_created_at_desc "
        "ON documents (org_id, created_at DESC)"
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_documents_org_sha256 ON documents (org_id, sha256)"
    )

    op.execute(
        """
        CREATE TABLE document_chunks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents ON DELETE CASCADE,
            org_id uuid NOT NULL,
            ordinal int NOT NULL,
            text text NOT NULL,
            token_count int NOT NULL,
            char_start int NOT NULL,
            char_end int NOT NULL,
            UNIQUE (document_id, ordinal)
        )
        """
    )
    op.execute("CREATE INDEX ix_document_chunks_org_id ON document_chunks (org_id)")

    op.execute(
        """
        CREATE TABLE chunk_embeddings (
            chunk_id uuid PRIMARY KEY REFERENCES document_chunks ON DELETE CASCADE,
            document_id uuid NOT NULL REFERENCES documents ON DELETE CASCADE,
            org_id uuid NOT NULL,
            embedding vector(768) NOT NULL,
            embedding_model text NOT NULL,
            dimensions int NOT NULL DEFAULT 768
                CHECK (dimensions = 768),
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_chunk_embeddings_org_id ON chunk_embeddings (org_id)")
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_hnsw ON chunk_embeddings "
        "USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)"
    )

    op.execute(
        """
        CREATE TABLE document_entities (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents ON DELETE CASCADE,
            org_id uuid NOT NULL,
            label text NOT NULL,
            text text NOT NULL,
            normalised text,
            taxonomy text,
            confidence numeric(4,3),
            char_start int NOT NULL,
            char_end int NOT NULL,
            rule_id text,
            source entity_source NOT NULL,
            is_pii boolean NOT NULL DEFAULT false,
            created_at timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_document_entities_document_id ON document_entities (document_id)"
    )
    op.execute(
        "CREATE INDEX ix_document_entities_org_label ON document_entities (org_id, label)"
    )
    op.execute(
        "CREATE INDEX ix_document_entities_normalised_gin "
        "ON document_entities USING gin (normalised gin_trgm_ops)"
    )


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only")

