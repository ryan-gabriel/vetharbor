"""Upload service — validation, extraction, persistence, outbox event."""

from __future__ import annotations

import json
from typing import Any

from app.core.auth import TenantContext
from app.core.errors import AppError, ErrorCode, ReadOnlyDemoError
from app.core.extraction import ExtractionError, extract_text
from app.core.mime import (
    MAX_UPLOAD_BYTES,
    MIME_TO_KIND,
    detect_mime,
    is_allowed_mime,
    is_archive_or_macro,
)
from app.modules.upload.repository import DocumentRepository
from app.persistence.db import Database

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
}


def _make_error(code: str, message: str) -> AppError:
    err = AppError(message)
    try:
        err.code = ErrorCode(code)
    except ValueError:
        err.code = ErrorCode.SERVER
    err.status = 422
    return err


class UploadService:
    def __init__(self, db: Database, demo_readonly: bool = False) -> None:
        self._db = db
        self._demo_readonly = demo_readonly

    async def upload(
        self,
        *,
        tenant: TenantContext,
        data: bytes,
        filename: str,
        declared_mime: str,
        kind: str | None = None,
    ) -> dict[str, Any]:
        # 1. Read-only demo check (server-side, regardless of UI).
        if self._demo_readonly:
            raise ReadOnlyDemoError()

        # 2. Size check.
        if not data:
            raise _make_error("not_found", "Empty file is not allowed.")
        if len(data) > MAX_UPLOAD_BYTES:
            raise _make_error(
                "not_found",
                f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
            )

        # 3. Archive / macro check.
        detected = detect_mime(data)
        if detected is None:
            raise _make_error("not_found", "Unsupported file type.")

        if is_archive_or_macro(detected, filename) or is_archive_or_macro(
            declared_mime, filename
        ):
            raise _make_error("not_found", "Archives and macro-enabled files are not allowed.")

        # 4. MIME allow-list + declared/detected agreement.
        if not is_allowed_mime(detected):
            raise _make_error("not_found", f"MIME type '{detected}' is not allowed.")
        if declared_mime and declared_mime != detected:
            raise _make_error(
                "not_found",
                f"Declared MIME '{declared_mime}' does not match detected '{detected}'.",
            )

        # 5. Determine kind.
        resolved_kind = kind or MIME_TO_KIND.get(detected, "cv")
        if resolved_kind not in {"cv", "proposal", "paper"}:
            resolved_kind = "cv"

        # 6. Sanitize filename (display only).
        safe_filename = _sanitize_filename(filename)

        # 7. Extract text in subprocess.
        try:
            result = extract_text(data, detected, safe_filename)
        except ExtractionError as exc:
            if exc.code == "encrypted":
                raise _make_error("not_found", "Encrypted documents are not supported.") from exc
            if exc.code == "pages_exceeded":
                raise _make_error("not_found", "Document exceeds 60 page limit.") from exc
            if exc.code == "empty":
                raise _make_error("not_found", "No text could be extracted.") from exc
            if exc.code == "timeout":
                raise _make_error("server", "Extraction timed out.") from exc
            raise _make_error("server", "Text extraction failed.") from exc

        # 8. Persist document + outbox event in one transaction.
        async with self._db.tenant_session(
            tenant_id=tenant.tenant_id,
            user_id=tenant.user_id,
            is_admin=tenant.is_admin,
        ) as session:
            repo = DocumentRepository(session)
            doc = await repo.create(
                org_id=tenant.tenant_id,
                kind=resolved_kind,
                filename=safe_filename,
                declared_mime=declared_mime or detected,
                detected_mime=detected,
                sha256=result.sha256,
                size_bytes=len(data),
                page_count=result.page_count,
                extracted_text=result.text,
                char_count=result.char_count,
                word_count=result.word_count,
                warning_flags=result.warning_flags,
                uploaded_by=tenant.user_id,
                status="ready",
            )
            # Outbox event in same transaction.
            import uuid as _uuid

            from sqlalchemy import text as sa_text

            await session.execute(
                sa_text(
                    "INSERT INTO outbox_events (event_id, org_id, aggregate_type, "
                    "aggregate_id, type, version, payload, status, occurred_at, "
                    "correlation_id) VALUES (:event_id, :org_id, 'document', "
                    ":aggregate_id, 'document.uploaded', 1, :payload, 'pending', "
                    "now(), :correlation_id)"
                ),
                {
                    "event_id": _uuid.uuid4(),
                    "org_id": tenant.tenant_id,
                    "aggregate_id": doc["id"],
                    "payload": json.dumps(
                        {"document_id": str(doc["id"]), "kind": resolved_kind}
                    ),
                    "correlation_id": None,
                },
            )
            return doc


def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for display only. Strip path components and dangerous chars."""
    import os

    # Strip any path components.
    name = os.path.basename(filename)
    # Remove null bytes and control chars.
    name = name.replace("\x00", "")
    name = "".join(c for c in name if c.isprintable() or c in " -_.")
    # Truncate to reasonable length.
    if len(name) > 255:
        name = name[:255]
    if not name:
        name = "unnamed"
    return name