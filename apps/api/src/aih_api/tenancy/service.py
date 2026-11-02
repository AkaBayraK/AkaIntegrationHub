from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aih_api.tenancy.models import IdentityProvider, Tenant


async def find_provider_by_issuer(session: AsyncSession, issuer: str) -> tuple[IdentityProvider, Tenant] | None:
    row = (
        await session.execute(
            select(IdentityProvider, Tenant)
            .join(Tenant, Tenant.id == IdentityProvider.tenant_id)
            .where(IdentityProvider.issuer == issuer, IdentityProvider.enabled, Tenant.enabled)
        )
    ).one_or_none()
    return None if row is None else (row[0], row[1])


async def find_tenant_by_slug(session: AsyncSession, slug: str) -> Tenant | None:
    return (await session.execute(select(Tenant).where(Tenant.slug == slug, Tenant.enabled))).scalar_one_or_none()


async def get_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> Tenant | None:
    return await session.get(Tenant, tenant_id)


async def upsert_tenant_with_issuer(
    session: AsyncSession,
    *,
    slug: str,
    name: str,
    issuer: str,
    client_ids: list[str],
    tenant_admin_roles: list[str],
    viewer_roles: list[str],
    platform_admin_roles: list[str] | None = None,
    jwks_uri: str | None = None,
) -> Tenant:
    tenant = await find_tenant_by_slug(session, slug)
    if tenant is None:
        tenant = Tenant(id=uuid.uuid4(), slug=slug, name=name)
        session.add(tenant)
        await session.flush()
    else:
        tenant.name = name
    provider = (
        await session.execute(select(IdentityProvider).where(IdentityProvider.issuer == issuer))
    ).scalar_one_or_none()
    if provider is None:
        provider = IdentityProvider(id=uuid.uuid4(), tenant_id=tenant.id, issuer=issuer, allowed_client_ids=[])
        session.add(provider)
    provider.tenant_id = tenant.id
    provider.allowed_client_ids = client_ids
    provider.tenant_admin_roles = tenant_admin_roles
    provider.viewer_roles = viewer_roles
    provider.platform_admin_roles = platform_admin_roles or []
    provider.jwks_uri = jwks_uri
    await session.flush()
    return tenant
