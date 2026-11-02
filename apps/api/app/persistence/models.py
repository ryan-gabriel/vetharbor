"""ORM models. Empty until the first M1 migration (DATA_MODEL.md §3).

Importing this module must register every model on ``Base.metadata`` so
Alembic autogenerate sees the full schema.
"""

from __future__ import annotations

from app.persistence.db import Base  # noqa: F401  (keeps the metadata hook explicit)
