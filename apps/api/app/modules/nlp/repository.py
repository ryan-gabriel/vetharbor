"""Entity repository — the only place that writes to document_entities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class EntityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_batch(
        self,
        *,
        document_id: uuid.UUID,
        org_id: uuid.UUID,
        entities: list[dict[str, Any]],
    ) -> int:
        if not entities:
            return 0
        now = datetime.now(UTC)
        for e in entities:
            await self._session.execute(
                text(
                    "INSERT INTO document_entities (id, document_id, org_id, label, "
                    "text, normalised, taxonomy, confidence, char_start, char_end, "
                    "rule_id, source, is_pii, created_at) "
                    "VALUES (:id, :document_id, :org_id, :label, :text, :normalised, "
                    ":taxonomy, :confidence, :char_start, :char_end, :rule_id, "
                    ":source, :is_pii, :created_at)"
                ),
                {
                    "id": uuid.uuid4(),
                    "document_id": document_id,
                    "org_id": org_id,
                    "label": e["label"],
                    "text": e["text"],
                    "normalised": e.get("normalised"),
                    "taxonomy": e.get("taxonomy"),
                    "confidence": e.get("confidence"),
                    "char_start": e["char_start"],
                    "char_end": e["char_end"],
                    "rule_id": e.get("rule_id"),
                    "source": e["source"],
                    "is_pii": e.get("is_pii", False),
                    "created_at": now,
                },
            )
        return len(entities)

    async def list_for_document(
        self, document_id: uuid.UUID, org_id: uuid.UUID
    ) -> list[dict[str, object]]:
        result = await self._session.execute(
            text(
                "SELECT id, label, text, normalised, taxonomy, confidence, "
                "char_start, char_end, rule_id, source, is_pii, created_at "
                "FROM document_entities WHERE document_id = :document_id "
                "AND org_id = :org_id ORDER BY char_start"
            ),
            {"document_id": document_id, "org_id": org_id},
        )
        return [dict(r) for r in result.mappings().all()]