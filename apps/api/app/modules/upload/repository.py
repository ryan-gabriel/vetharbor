"""Document repository — the only place that writes to the documents table."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession


class DocumentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        org_id: uuid.UUID,
        kind: str,
        filename: str,
        declared_mime: str,
        detected_mime: str,
        sha256: str,
        size_bytes: int,
        page_count: int | None,
        extracted_text: str,
        char_count: int,
        word_count: int,
        warning_flags: list[str],
        uploaded_by: uuid.UUID | None,
        status: str = "ready",
    ) -> dict[str, object]:
        from sqlalchemy import text

        doc_id = uuid.uuid4()
        now = datetime.now(UTC)
        await self._session.execute(
            text(
                "INSERT INTO documents (id, org_id, kind, filename, declared_mime, "
                "detected_mime, sha256, size_bytes, page_count, extracted_text, "
                "char_count, word_count, status, warning_flags, uploaded_by, "
                "created_at, updated_at) "
                "VALUES (:id, :org_id, :kind, :filename, :declared_mime, "
                ":detected_mime, :sha256, :size_bytes, :page_count, :extracted_text, "
                ":char_count, :word_count, :status, :warning_flags, :uploaded_by, "
                ":created_at, :updated_at)"
            ),
            {
                "id": doc_id,
                "org_id": org_id,
                "kind": kind,
                "filename": filename,
                "declared_mime": declared_mime,
                "detected_mime": detected_mime,
                "sha256": sha256,
                "size_bytes": size_bytes,
                "page_count": page_count,
                "extracted_text": extracted_text,
                "char_count": char_count,
                "word_count": word_count,
                "status": status,
                "warning_flags": warning_flags,
                "uploaded_by": uploaded_by,
                "created_at": now,
                "updated_at": now,
            },
        )
        return {
            "id": doc_id,
            "org_id": org_id,
            "kind": kind,
            "filename": filename,
            "status": status,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "page_count": page_count,
            "char_count": char_count,
            "word_count": word_count,
            "warning_flags": warning_flags,
            "created_at": now,
            "updated_at": now,
        }

    async def get(self, document_id: uuid.UUID, org_id: uuid.UUID) -> dict[str, object] | None:
        from sqlalchemy import text

        result = await self._session.execute(
            text(
                "SELECT id, org_id, kind, filename, status, sha256, size_bytes, "
                "page_count, extracted_text, char_count, word_count, warning_flags, "
                "created_at, updated_at FROM documents "
                "WHERE id = :id AND org_id = :org_id"
            ),
            {"id": document_id, "org_id": org_id},
        )
        row = result.mappings().first()
        return dict(row) if row else None

    async def list_for_org(
        self, org_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> tuple[list[dict[str, object]], int]:
        from sqlalchemy import text

        offset = (page - 1) * page_size
        result = await self._session.execute(
            text(
                "SELECT id, org_id, kind, filename, status, sha256, size_bytes, "
                "page_count, extracted_text, char_count, word_count, warning_flags, "
                "created_at, updated_at FROM documents "
                "WHERE org_id = :org_id ORDER BY created_at DESC "
                "LIMIT :limit OFFSET :offset"
            ),
            {"org_id": org_id, "limit": page_size, "offset": offset},
        )
        items = [dict(r) for r in result.mappings().all()]
        count_result = await self._session.execute(
            text("SELECT count(*) FROM documents WHERE org_id = :org_id"),
            {"org_id": org_id},
        )
        total = count_result.scalar_one()
        return items, total