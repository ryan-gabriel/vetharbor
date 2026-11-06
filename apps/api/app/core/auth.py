"""Tenant resolution dependency.

M1 uses a development placeholder: a fixed tenant, user and admin flag. M3
replaces this with OIDC verification and ``org_memberships`` resolution
(ADR-006). The placeholder is intentionally obvious so it cannot be mistaken
for production auth.

One safety rule here is permanent: ``X-Dev-Tenant-Id`` exists so the isolation
tests can act as tenant A and then tenant B. Trusting it in ``prod`` would let
any caller name any tenant, which is exactly what AGENTS.md §3.9 forbids, so it
is ignored outside dev/test. When M3 lands, this header disappears with the
rest of the placeholder.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header, Request

from app.core.config import Settings

# Fixed dev tenant used until M3 wires real OIDC + memberships.
DEV_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEV_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    is_admin: bool


def dev_header_allowed(environment: str) -> bool:
    """Only ``dev`` and ``test`` may impersonate a tenant via header."""
    return environment in {"dev", "test"}


def resolve_tenant_from(settings: Settings, x_dev_tenant_id: str | None) -> TenantContext:
    """Pure resolution, so the prod rule is unit-testable without a request."""
    tenant_id = DEV_TENANT_ID
    if x_dev_tenant_id and dev_header_allowed(settings.environment):
        with contextlib.suppress(ValueError):
            tenant_id = uuid.UUID(x_dev_tenant_id)
    return TenantContext(tenant_id=tenant_id, user_id=DEV_USER_ID, is_admin=True)


async def resolve_tenant(
    request: Request,
    x_dev_tenant_id: str | None = Header(default=None, alias="X-Dev-Tenant-Id"),
) -> TenantContext:
    """Resolve the active tenant for the request.

    Reads settings from ``app.state`` so the value the application was built
    with wins over the process environment (tests inject ``environment=test``).
    """
    settings: Settings = request.app.state.settings
    return resolve_tenant_from(settings, x_dev_tenant_id)


TenantDep = Annotated[TenantContext, Depends(resolve_tenant)]
