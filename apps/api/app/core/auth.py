"""Tenant resolution dependency.

M1 uses a development placeholder: a fixed tenant, user and admin flag. M3
replaces this with OIDC verification and ``org_memberships`` resolution
(ADR-006). The placeholder is intentionally obvious so it cannot be mistaken
for production auth.
"""

from __future__ import annotations

import contextlib
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header

# Fixed dev tenant used until M3 wires real OIDC + memberships.
DEV_TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
DEV_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@dataclass(frozen=True)
class TenantContext:
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    is_admin: bool


async def resolve_tenant(
    x_dev_tenant_id: str | None = Header(default=None, alias="X-Dev-Tenant-Id"),
) -> TenantContext:
    """Resolve the active tenant for the request.

    M1 dev placeholder: returns a fixed tenant unless ``X-Dev-Tenant-Id`` is
    supplied (used by tests to exercise cross-tenant isolation). M3 replaces
    this entirely with OIDC + ``org_memberships``.
    """
    tenant_id = DEV_TENANT_ID
    if x_dev_tenant_id:
        with contextlib.suppress(ValueError):
            tenant_id = uuid.UUID(x_dev_tenant_id)
    return TenantContext(tenant_id=tenant_id, user_id=DEV_USER_ID, is_admin=True)


TenantDep = Annotated[TenantContext, Depends(resolve_tenant)]