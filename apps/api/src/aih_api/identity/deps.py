"""FastAPI bağımlılıkları: kimlik, izin ve tenant kapsamı."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, HTTPException, Path, Request

from aih_api.db import Database
from aih_api.identity.principal import Permission, Principal, Role
from aih_api.identity.verifier import AuthenticationError, TokenVerifier
from aih_api.tenancy import service as tenancy

DEV_USER_HEADER = "X-AIH-Dev-User"


def _unauthorized() -> HTTPException:
    return HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})


async def _dev_principal(request: Request, value: str) -> Principal:
    # Biçim: "<tenant-slug>:<Rol>[,<Rol>]" — yalnız local/test ortamında ve açıkça etkinleştirildiğinde.
    slug, _, role_text = value.partition(":")
    try:
        roles = frozenset(Role(r.strip()) for r in role_text.split(",") if r.strip())
    except ValueError as exc:
        raise _unauthorized() from exc
    db: Database = request.app.state.db
    async with db.transaction() as session:
        tenant = await tenancy.find_tenant_by_slug(session, slug)
    if tenant is None:
        raise _unauthorized()
    return Principal(subject=f"dev:{slug}", issuer="aih-dev", tenant_id=tenant.id, tenant_slug=tenant.slug, roles=roles)


async def current_principal(request: Request) -> Principal:
    settings = request.app.state.settings
    dev_value = request.headers.get(DEV_USER_HEADER)
    if dev_value is not None and settings.auth_dev_mode:
        return await _dev_principal(request, dev_value)

    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized()
    db: Database = request.app.state.db
    verifier: TokenVerifier = request.app.state.token_verifier

    async def lookup(issuer: str) -> Any:
        async with db.transaction() as session:
            return await tenancy.find_provider_by_issuer(session, issuer)

    try:
        return await verifier.verify(token.strip(), lookup)
    except AuthenticationError as exc:
        raise _unauthorized() from exc


CurrentPrincipal = Annotated[Principal, Depends(current_principal)]


@dataclass(frozen=True)
class TenantScope:
    principal: Principal
    tenant_id: uuid.UUID


def require(permission: Permission) -> Callable[..., Awaitable[TenantScope]]:
    """Path'teki ``tenantId`` için izin kontrolü.

    Path değeri yetki kaynağı değildir: kimlikteki tenant ile eşleşmezse (PlatformAdmin hariç) 404 döner,
    böylece başka tenant'ın varlığı sızdırılmaz.
    """

    async def dependency(
        principal: CurrentPrincipal, tenant_id: Annotated[uuid.UUID, Path(alias="tenantId")]
    ) -> TenantScope:
        if tenant_id != principal.tenant_id and not principal.is_platform_admin:
            raise HTTPException(404, "Not Found")
        if not principal.can(permission):
            raise HTTPException(403, "Forbidden")
        return TenantScope(principal=principal, tenant_id=tenant_id)

    return dependency
