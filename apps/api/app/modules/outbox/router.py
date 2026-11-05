"""Public HTTP surface for the outbox module."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.auth import TenantDep
from app.modules.outbox.service import OutboxDrainService
from app.persistence.db import Database

router = APIRouter(prefix="/outbox", tags=["outbox"])


def _get_db(request: Request) -> Database:
    db: Database = request.app.state.db
    return db


@router.post("/drain", status_code=200)
async def drain_outbox(
    tenant: TenantDep,
    request: Request,
) -> dict[str, object]:
    """Trigger one bounded drain pass (lite profile). No polling."""
    db = _get_db(request)
    service = OutboxDrainService(db=db, batch_size=20)
    result = await service.drain(tenant_id=tenant.tenant_id)
    return {
        "claimed": result.claimed,
        "processed": result.processed,
        "failed": result.failed,
        "skipped": result.skipped,
        "event_ids": result.event_ids,
    }