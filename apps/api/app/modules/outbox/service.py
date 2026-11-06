"""Outbox drain service — bounded, on-demand, no polling (AGENTS.md §3.6).

Lite profile: the API drains pending events on demand (admin endpoint or
after upload). Full profile: a Spring worker claims events via SKIP LOCKED.
Both use the same event schema and idempotency contract.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.db import Database


@dataclass
class DrainResult:
    claimed: int = 0
    processed: int = 0
    failed: int = 0
    skipped: int = 0
    event_ids: list[str] = field(default_factory=list)


class OutboxDrainService:
    """Bounded drain: claims up to ``batch_size`` pending events and processes
    them in a single pass. No loop, no sleep, no background thread."""

    def __init__(self, db: Database, batch_size: int = 20) -> None:
        self._db = db
        self._batch_size = batch_size

    async def drain(
        self,
        *,
        tenant_id: uuid.UUID | None = None,
        cross_tenant: bool = False,
    ) -> DrainResult:
        """Claim and process up to ``batch_size`` pending events.

        ``cross_tenant=True`` uses the worker role semantics (bypasses RLS)
        for the full-profile orchestrator. Lite mode always drains within a
        single tenant context.
        """
        result = DrainResult()

        if cross_tenant:
            # Worker role bypasses RLS on outbox_events.
            async with self._db.session_factory() as session, session.begin():
                claimed = await self._claim_events(session, tenant_id=None)
                for event in claimed:
                    result.event_ids.append(str(event["event_id"]))
                    result.claimed += 1
                    try:
                        await self._process_event(session, event)
                        await self._mark_done(session, event["id"])
                        result.processed += 1
                    except Exception:
                        await self._mark_failed(session, event)
                        result.failed += 1
        else:
            if tenant_id is None:
                return result
            async with self._db.tenant_session(
                tenant_id=tenant_id,
                user_id=None,
                is_admin=True,
            ) as session:
                claimed = await self._claim_events(session, tenant_id=tenant_id)
                for event in claimed:
                    result.event_ids.append(str(event["event_id"]))
                    result.claimed += 1
                    try:
                        await self._process_event(session, event)
                        await self._mark_done(session, event["id"])
                        result.processed += 1
                    except Exception:
                        await self._mark_failed(session, event)
                        result.failed += 1

        return result

    async def _claim_events(
        self, session: AsyncSession, tenant_id: uuid.UUID | None
    ) -> list[dict[str, Any]]:
        """Claim up to batch_size pending events using SKIP LOCKED."""
        if tenant_id is not None:
            query = text(
                "UPDATE outbox_events SET status = 'claimed', claimed_at = now(), "
                "claimed_by = 'api-drain' WHERE id IN ("
                "  SELECT id FROM outbox_events "
                "  WHERE status = 'pending' AND org_id = :org_id "
                "  ORDER BY id LIMIT :limit "
                "  FOR UPDATE SKIP LOCKED"
                ") RETURNING id, event_id, org_id, aggregate_type, aggregate_id, "
                "type, version, payload, attempts, correlation_id"
            )
            params = {"org_id": tenant_id, "limit": self._batch_size}
        else:
            query = text(
                "UPDATE outbox_events SET status = 'claimed', claimed_at = now(), "
                "claimed_by = 'worker-drain' WHERE id IN ("
                "  SELECT id FROM outbox_events "
                "  WHERE status = 'pending' "
                "  ORDER BY id LIMIT :limit "
                "  FOR UPDATE SKIP LOCKED"
                ") RETURNING id, event_id, org_id, aggregate_type, aggregate_id, "
                "type, version, payload, attempts, correlation_id"
            )
            params = {"limit": self._batch_size}

        result = await session.execute(query, params)
        return [dict(r) for r in result.mappings().all()]

    async def _process_event(self, session: AsyncSession, event: dict[str, Any]) -> None:
        """Process a single event. Idempotent: checks idempotency_keys first."""
        event_id = event["event_id"]
        # Check idempotency.
        result = await session.execute(
            text("SELECT 1 FROM idempotency_keys WHERE event_id = :eid"),
            {"eid": event_id},
        )
        if result.scalar_one_or_none() is not None:
            # Already processed — no-op.
            return

        # For document.uploaded: entities already persisted during upload.
        # Just record idempotency.
        await session.execute(
            text(
                "INSERT INTO idempotency_keys (event_id, consumer, result_status, "
                "result_ref) VALUES (:eid, 'api-drain', 'ok', :ref)"
            ),
            {"eid": event_id, "ref": json.dumps(event.get("payload", {}))},
        )

    async def _mark_done(self, session: AsyncSession, event_pk: int) -> None:
        await session.execute(
            text("UPDATE outbox_events SET status = 'done', completed_at = now() WHERE id = :id"),
            {"id": event_pk},
        )

    async def _mark_failed(self, session: AsyncSession, event: dict[str, Any]) -> None:
        event_pk = event["id"]
        attempts = event.get("attempts", 0) + 1
        if attempts >= 3:
            # Move to DLQ.
            await session.execute(
                text(
                    "INSERT INTO dead_letter_events (event_id, org_id, reason, "
                    "last_error, attempts, payload, failed_at) "
                    "VALUES (:eid, :org_id, :reason, :err, :attempts, :payload, now()) "
                    "ON CONFLICT (event_id) DO NOTHING"
                ),
                {
                    "eid": event["event_id"],
                    "org_id": event["org_id"],
                    "reason": "processing_failed",
                    "err": "processing error",
                    "attempts": attempts,
                    "payload": json.dumps(event.get("payload", {})),
                },
            )
            await session.execute(
                text(
                    "UPDATE outbox_events SET status = 'failed', attempts = :attempts "
                    "WHERE id = :id"
                ),
                {"attempts": attempts, "id": event_pk},
            )
        else:
            await session.execute(
                text(
                    "UPDATE outbox_events SET status = 'pending', attempts = :attempts "
                    "WHERE id = :id"
                ),
                {"attempts": attempts, "id": event_pk},
            )
