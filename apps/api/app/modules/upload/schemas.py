"""Pydantic schemas for the upload module."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    kind: str
    filename: str
    status: str
    sha256: str
    size_bytes: int
    page_count: int | None
    char_count: int
    word_count: int
    warning_flags: list[str]
    created_at: datetime | None


class DocumentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    org_id: uuid.UUID
    kind: str
    filename: str
    status: str
    sha256: str
    size_bytes: int
    page_count: int | None
    extracted_text: str
    char_count: int
    word_count: int
    warning_flags: list[str]
    created_at: datetime | None
    updated_at: datetime | None


class DocumentListResponse(BaseModel):
    items: list[DocumentDetail]
    total: int
    page: int
    page_size: int