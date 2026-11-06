"""Public HTTP surface for the upload module."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.auth import TenantDep
from app.core.errors import NotFoundError
from app.core.mime import MAX_UPLOAD_BYTES
from app.modules.upload.schemas import DocumentDetail, DocumentListResponse, DocumentUploadResponse
from app.modules.upload.service import UploadService
from app.persistence.db import Database

router = APIRouter(prefix="/documents", tags=["documents"])

# Module-level singleton for the File(...) default (ruff B008).
_UPLOAD_FILE = File(...)


def _get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


@router.post("", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    tenant: TenantDep,
    file: UploadFile = _UPLOAD_FILE,
    kind: str | None = Form(default=None),
    request: Request = None,  # type: ignore[assignment]
) -> DocumentUploadResponse:
    db = _get_db(request)
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    service = UploadService(db=db, demo_readonly=False)
    doc = await service.upload(
        tenant=tenant,
        data=data,
        filename=file.filename or "unnamed",
        declared_mime=file.content_type or "application/octet-stream",
        kind=kind,
    )
    return DocumentUploadResponse(**doc)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    tenant: TenantDep,
    page: int = 1,
    page_size: int = 20,
    request: Request = None,  # type: ignore[assignment]
) -> DocumentListResponse:
    db = _get_db(request)
    async with db.tenant_session(
        tenant_id=tenant.tenant_id,
        user_id=tenant.user_id,
        is_admin=tenant.is_admin,
    ) as session:
        from app.modules.upload.repository import DocumentRepository

        repo = DocumentRepository(session)
        items, total = await repo.list_for_org(tenant.tenant_id, page, page_size)
        return DocumentListResponse(
            items=[DocumentDetail(**item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
        )


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: uuid.UUID,
    tenant: TenantDep,
    request: Request = None,  # type: ignore[assignment]
) -> DocumentDetail:
    db = _get_db(request)
    async with db.tenant_session(
        tenant_id=tenant.tenant_id,
        user_id=tenant.user_id,
        is_admin=tenant.is_admin,
    ) as session:
        from app.modules.upload.repository import DocumentRepository

        repo = DocumentRepository(session)
        doc = await repo.get(document_id, tenant.tenant_id)
        if doc is None:
            raise NotFoundError("Document not found.")
        return DocumentDetail(**doc)
