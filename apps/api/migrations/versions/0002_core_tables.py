"""0002 — Core tables: orgs, users, org_memberships, job_roles.

Logical change: create the tenant root, mirrored OIDC identity, tenancy spine,
and first-class job role tables with their foreign keys, constraints and
indexes.

job_roles.embedding is vector(768) and nullable (populated later by the
scoring pipeline); embedding_model must be present whenever an embedding is.
The unique (org_id, lower(title)) index is partial on deleted_at IS NULL so
only active roles dedupe by title.

Forward-only: no downgrade.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_core_tables"
down_revision = "0001_ext_enums"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE orgs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL UNIQUE,
            slug text NOT NULL UNIQUE,
            is_demo boolean NOT NULL DEFAULT false,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            issuer text NOT NULL,
            subject text NOT NULL,
            email citext,
            display_name text,
            last_login_at timestamptz,
            created_at timestamptz NOT NULL DEFAULT now(),
            updated_at timestamptz NOT NULL DEFAULT now(),
            UNIQUE (issuer, subject)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE org_memberships (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL REFERENCES orgs ON DELETE CASCADE,
            user_id uuid NOT NULL REFERENCES users ON DELETE CASCADE,
            role user_role NOT NULL,
            status membership_status NOT NULL DEFAULT 'active',
            invited_by uuid REFERENCES users,
            created_at timestamptz,
            updated_at timestamptz,
            revoked_at timestamptz,
            UNIQUE (org_id, user_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX org_memberships_active_user_idx "
        "ON org_memberships (user_id) WHERE status = 'active'"
    )
    op.execute(
        """
        CREATE TABLE job_roles (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            org_id uuid NOT NULL REFERENCES orgs ON DELETE CASCADE,
            title text NOT NULL,
            description text NOT NULL,
            required_skills text[] NOT NULL DEFAULT '{}',
            nice_to_have_skills text[] NOT NULL DEFAULT '{}',
            min_years_experience numeric(4,1) NOT NULL DEFAULT 0
                CHECK (min_years_experience >= 0),
            embedding vector(768) NULL,
            embedding_model text NULL,
            status job_role_status NOT NULL DEFAULT 'open',
            created_by uuid REFERENCES users,
            created_at timestamptz,
            updated_at timestamptz,
            deleted_at timestamptz,
            CONSTRAINT job_roles_embedding_requires_model
                CHECK (embedding IS NULL OR embedding_model IS NOT NULL)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX job_roles_active_title_unique "
        "ON job_roles (org_id, lower(title)) WHERE deleted_at IS NULL"
    )
    op.execute(
        "CREATE INDEX ix_job_roles_org_id ON job_roles (org_id)"
    )


def downgrade() -> None:
    raise NotImplementedError("migrations are forward-only")

