from __future__ import annotations

import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from aih_api.db import Database
from aih_api.errors import ApiError
from aih_api.identity.deps import CurrentPrincipal
from aih_api.tenancy import service as tenancy

router = APIRouter(prefix="/v1", tags=["identity"])


class TenantRef(BaseModel):
    id: uuid.UUID
    slug: str
    name: str


class Me(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    subject: str
    display_name: str | None = Field(alias="displayName")
    email: str | None
    tenant: TenantRef
    roles: list[str]
    permissions: list[str]


@router.get("/me", response_model=Me)
async def me(principal: CurrentPrincipal, request: Request) -> Me:
    db: Database = request.app.state.db
    async with db.transaction() as session:
        tenant = await tenancy.get_tenant(session, principal.tenant_id)
    if tenant is None:
        raise ApiError(404, "AIH-COMMON-404", "Tenant bulunamadı")
    return Me(
        subject=principal.subject,
        display_name=principal.display_name,
        email=principal.email,
        tenant=TenantRef(id=tenant.id, slug=tenant.slug, name=tenant.name),
        roles=sorted(r.value for r in principal.roles),
        permissions=sorted(p.value for p in principal.permissions),
    )
