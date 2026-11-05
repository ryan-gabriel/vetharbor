"""0004 — Scoring, outbox, RAG, audit and security-eval tables.

Logical change: create model_versions, scores, shadow_scores, outbox_events,
dead_letter_events, idempotency_keys, rag_queries, audit_log,
security_eval_runs and demo_state.

scores/shadow_scores/audit_log are append-only for the application role
(enforced by grants in 0005, not by table constraints, so the database itself
rejects mutations at the role level).

security_eval_runs CHECK constraints encode SPEC.md §9 thresholds, so a CI run
cannot persist a row that violates a guardrail gate.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_scoring_outbox_rag_audit"
down_revision = "0003_documents_chunks_entities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE model_versions (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            version text NOT NULL,
            algorithm text NOT NULL,
            artifact_path text NOT NULL,
            params jsonb NOT NULL DEFAULT '{}',
            features text[] NOT NULL,
            excluded_features text[] NOT NULL,
            metrics jsonb NOT NULL,
            dataset_ref text NOT NULL,
            model_card_path text NOT NULL,
            is_active boolean NOT NULL DEFAULT false,
            is_shadow boolean NOT NULL DEFAULT false,
            trained_at timestamptz NOT NULL,
            UNIQUE (name, version)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX ix_model_versions_active_name "
        "ON model_versions (name) WHERE is_active"
    )

    op.execute(
        """
        CREATE TABLE scores (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL,
            document_id uuid NOT NULL REFERENCES documents ON DELETE CASCADE,
            job_role_id uuid NOT NULL REFERENCES job_roles ON DELETE RESTRICT,
            model_version_id uuid NOT NULL REFERENCES model_versions,
            role_match_score numeric(5,4) NOT NULL
                CHECK (role_match_score >= 0 AND role_match_score <= 1),
            band score_band NOT NULL,
            feature_skill_overlap numeric(5,4) NOT NULL,
            feature_years_experience numeric(5,4) NOT NULL,
            feature_embedding_similarity numeric(5,4) NOT NULL,
            calibration jsonb,
            evidence jsonb NOT NULL,
            rank_in_query int,
            requested_by uuid REFERENCES users,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_scores_org_role_score_desc "
        "ON scores (org_id, job_role_id, role_match_score DESC)"
    )
    op.execute(
        "CREATE INDEX ix_scores_document_model ON scores (document_id, model_version_id)"
    )

    op.execute(
        """
        CREATE TABLE shadow_scores (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL,
            document_id uuid NOT NULL REFERENCES documents ON DELETE CASCADE,
            job_role_id uuid NOT NULL REFERENCES job_roles ON DELETE RESTRICT,
            model_version_id uuid NOT NULL REFERENCES model_versions,
            role_match_score numeric(5,4) NOT NULL
                CHECK (role_match_score >= 0 AND role_match_score <= 1),
            band score_band NOT NULL,
            feature_skill_overlap numeric(5,4) NOT NULL,
            feature_years_experience numeric(5,4) NOT NULL,
            feature_embedding_similarity numeric(5,4) NOT NULL,
            calibration jsonb,
            evidence jsonb NOT NULL,
            rank_in_query int,
            requested_by uuid REFERENCES users,
            compared_to_score_id uuid NOT NULL REFERENCES scores,
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE outbox_events (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            event_id uuid NOT NULL UNIQUE,
            org_id uuid NOT NULL,
            aggregate_type text NOT NULL,
            aggregate_id uuid NOT NULL,
            type event_type NOT NULL,
            version int NOT NULL DEFAULT 1,
            payload jsonb NOT NULL,
            status outbox_status NOT NULL DEFAULT 'pending',
            attempts int NOT NULL DEFAULT 0 CHECK (attempts BETWEEN 0 AND 3),
            claimed_at timestamptz,
            claimed_by text,
            correlation_id text,
            occurred_at timestamptz NOT NULL,
            completed_at timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_outbox_events_claim ON outbox_events (status, id) "
        "WHERE status = 'pending'"
    )

    op.execute(
        """
        CREATE TABLE dead_letter_events (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            event_id uuid NOT NULL UNIQUE REFERENCES outbox_events,
            org_id uuid NOT NULL,
            reason text NOT NULL,
            last_error text,
            attempts int NOT NULL,
            payload jsonb NOT NULL,
            failed_at timestamptz NOT NULL,
            resolved_at timestamptz,
            resolved_by uuid
        )
        """
    )

    op.execute(
        """
        CREATE TABLE idempotency_keys (
            event_id uuid PRIMARY KEY REFERENCES outbox_events ON DELETE CASCADE,
            consumer text NOT NULL,
            result_status text NOT NULL,
            result_ref jsonb,
            processed_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE rag_queries (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL,
            asked_by uuid REFERENCES users,
            question text NOT NULL,
            retrieved_chunk_ids uuid[] NOT NULL DEFAULT '{}',
            answer text,
            outcome rag_outcome NOT NULL,
            guardrails jsonb NOT NULL DEFAULT '{}',
            llm_provider text NOT NULL,
            llm_model text NOT NULL,
            latency_ms int,
            correlation_id text,
            created_at timestamptz
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_rag_queries_org_created_at_desc "
        "ON rag_queries (org_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_rag_queries_guardrails_gin "
        "ON rag_queries USING gin (guardrails jsonb_path_ops)"
    )

    op.execute(
        """
        CREATE TABLE audit_log (
            id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            org_id uuid NOT NULL,
            actor_user_id uuid REFERENCES users,
            action text NOT NULL,
            target_type text,
            target_id text,
            result audit_result NOT NULL,
            ip inet,
            correlation_id text,
            metadata jsonb NOT NULL DEFAULT '{}',
            created_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX ix_audit_log_org_created_at_desc "
        "ON audit_log (org_id, created_at DESC)"
    )
    op.execute(
        "CREATE INDEX ix_audit_log_org_action ON audit_log (org_id, action)"
    )

    op.execute(
        """
        CREATE TABLE security_eval_runs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            run_at timestamptz NOT NULL,
            corpus_version text NOT NULL,
            corpus_size int NOT NULL CHECK (corpus_size >= 50),
            block_rate numeric(5,4) NOT NULL CHECK (block_rate >= 0.95),
            false_positive_rate numeric(5,4) NOT NULL
                CHECK (false_positive_rate <= 0.05),
            canary_leaks int NOT NULL CHECK (canary_leaks = 0),
            pii_recall numeric(5,4) NOT NULL CHECK (pii_recall >= 0.99),
            cross_tenant_chunks int NOT NULL CHECK (cross_tenant_chunks = 0),
            provider text NOT NULL,
            ci_run_url text
        )
        """
    )

    op.execute(
        """
        CREATE TABLE demo_state (
            id int PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            last_seed_at timestamptz,
            seeded_document_count int,
            is_readonly_mode boolean NOT NULL DEFAULT true,
            updated_at timestamptz
        )
        """
    )
    op.execute(
        "INSERT INTO demo_state (is_readonly_mode) VALUES (true)"
    )


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only")

