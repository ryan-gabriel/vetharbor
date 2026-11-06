"""Pydantic schemas for the NLP module."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict


class EntityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID | None = None
    label: str
    text: str
    normalised: str | None = None
    taxonomy: str | None = None
    confidence: float | None = None
    char_start: int
    char_end: int
    rule_id: str | None = None
    source: str
    is_pii: bool = False


class NLPProcessResult(BaseModel):
    document_id: uuid.UUID
    entity_count: int
    pipeline_version: str
    entities: list[EntityOut]
