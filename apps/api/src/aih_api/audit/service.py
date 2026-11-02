from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from aih_api.identity.principal import Principal
from aih_common import correlation
from aih_common.logging import redact_sensitive


async def record(
    session: AsyncSession,
    principal: Principal,
    *,
    action: str,
    resource_type: str,
    resource_id: str | uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    outcome: str = "success",
    details: dict[str, Any] | None = None,
) -> None:
    """Audit kaydı yazar. ``details`` sır içermemelidir; yine de anahtar adına göre maskelenir."""
    safe = dict(redact_sensitive(None, "audit", dict(details or {})))
    if principal.is_platform_admin and tenant_id is not None and tenant_id != principal.tenant_id:
        safe["breakGlass"] = True
    await session.execute(
        text(
            "INSERT INTO audit.audit_events (id, tenant_id, actor_subject, actor_issuer, actor_via, action,"
            " resource_type, resource_id, outcome, correlation_id, details)"
            " VALUES (:id, :tenant_id, :subject, :issuer, :via, :action, :rtype, :rid, :outcome, :cid,"
            " CAST(:details AS jsonb))"
        ),
        {
            "id": uuid.uuid4(),
            "tenant_id": tenant_id or principal.tenant_id,
            "subject": principal.subject,
            "issuer": principal.issuer,
            "via": principal.via,
            "action": action,
            "rtype": resource_type,
            "rid": None if resource_id is None else str(resource_id),
            "outcome": outcome,
            "cid": correlation.current(),
            "details": json.dumps(safe, default=str),
        },
    )
