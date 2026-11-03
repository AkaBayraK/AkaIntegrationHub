from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from aih_api.db import Database
from aih_api.identity.deps import CurrentPrincipal, TenantScope, require
from aih_api.identity.principal import Permission
from aih_api.providers.cache import service
from aih_api.providers.cache.capabilities import CACHE_CAPABILITIES
from aih_api.providers.cache.models import CacheAccount
from aih_api.providers.cache.schemas import (
    CacheAccountCreate,
    CacheAccountOut,
    CacheAccountPage,
    CacheAccountUpdate,
    CacheCapabilityOut,
    CacheConnectionTestOut,
    CacheServerInfo,
    CacheTestStep,
)
from aih_api.providers.common import mask, parse_if_match

router = APIRouter(prefix="/v1", tags=["cache"])
BASE = "/tenants/{tenantId}/cache-accounts"

AccountId = Annotated[uuid.UUID, Path(alias="accountId")]
ReadScope = Annotated[TenantScope, Depends(require(Permission.CACHE_ACCOUNT_READ))]
WriteScope = Annotated[TenantScope, Depends(require(Permission.CACHE_ACCOUNT_WRITE))]
TestScope = Annotated[TenantScope, Depends(require(Permission.CACHE_ACCOUNT_TEST))]
IfMatch = Annotated[str | None, Header(alias="If-Match")]


@asynccontextmanager
async def cache_context(request: Request, scope: TenantScope) -> AsyncIterator[service.CacheContext]:
    db: Database = request.app.state.db
    async with db.transaction(scope.tenant_id) as session:
        yield service.CacheContext(
            session=session,
            principal=scope.principal,
            tenant_id=scope.tenant_id,
            secrets=request.app.state.secret_store,
            policy=request.app.state.cache_policy,
        )


def _out(account: CacheAccount, scope: TenantScope) -> CacheAccountOut:
    fields = {name: getattr(account, name) for name in CacheAccountOut.model_fields if name != "has_secret"}
    out = CacheAccountOut.model_validate({**fields, "has_secret": account.secret_ref is not None})
    if not scope.principal.can(Permission.CACHE_ACCOUNT_WRITE):
        out = out.model_copy(update={"host": mask(out.host) or "", "username": mask(out.username)})
    return out


def _etag(response: Response, account: CacheAccount) -> None:
    response.headers["ETag"] = f'W/"{account.version}"'


@router.get("/provider-types/cache", response_model=list[CacheCapabilityOut], response_model_by_alias=True)
async def capabilities(_: CurrentPrincipal) -> list[CacheCapabilityOut]:
    return [
        CacheCapabilityOut(type=c.type, label=c.label, default_port=c.default_port, license_note=c.license_note)
        for c in CACHE_CAPABILITIES.values()
    ]


@router.get(BASE, response_model=CacheAccountPage, response_model_by_alias=True)
async def list_accounts(
    request: Request,
    scope: ReadScope,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> CacheAccountPage:
    async with cache_context(request, scope) as ctx:
        rows, next_cursor = await service.list_accounts(ctx, search=q, limit=limit, cursor=cursor)
        return CacheAccountPage(items=[_out(r, scope) for r in rows], next_cursor=next_cursor)


@router.post(BASE, response_model=CacheAccountOut, response_model_by_alias=True, status_code=201)
async def create_account(
    request: Request, response: Response, payload: CacheAccountCreate, scope: WriteScope
) -> CacheAccountOut:
    async with cache_context(request, scope) as ctx:
        account = await service.create(ctx, payload)
        _etag(response, account)
        response.headers["Location"] = f"/v1/tenants/{scope.tenant_id}/cache-accounts/{account.id}"
        return _out(account, scope)


@router.get(BASE + "/{accountId}", response_model=CacheAccountOut, response_model_by_alias=True)
async def get_account(request: Request, response: Response, account_id: AccountId, scope: ReadScope) -> CacheAccountOut:
    async with cache_context(request, scope) as ctx:
        account = await service.get(ctx, account_id)
        _etag(response, account)
        return _out(account, scope)


@router.patch(BASE + "/{accountId}", response_model=CacheAccountOut, response_model_by_alias=True)
async def update_account(
    request: Request,
    response: Response,
    account_id: AccountId,
    payload: CacheAccountUpdate,
    scope: WriteScope,
    if_match: IfMatch = None,
) -> CacheAccountOut:
    expected = parse_if_match(if_match)
    async with cache_context(request, scope) as ctx:
        account = await service.update_account(ctx, account_id, payload, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/make-default", response_model=CacheAccountOut, response_model_by_alias=True)
async def make_default(
    request: Request, response: Response, account_id: AccountId, scope: WriteScope, if_match: IfMatch = None
) -> CacheAccountOut:
    expected = parse_if_match(if_match)
    async with cache_context(request, scope) as ctx:
        account = await service.make_default(ctx, account_id, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/test-connection", response_model=CacheConnectionTestOut, response_model_by_alias=True)
async def test_connection(request: Request, account_id: AccountId, scope: TestScope) -> CacheConnectionTestOut:
    async with cache_context(request, scope) as ctx:
        result = await service.test_connection(ctx, account_id)
    return CacheConnectionTestOut(
        account_id=result.account_id,
        outcome=result.outcome,
        error_code=result.error_code,
        steps=[CacheTestStep.model_validate(step.as_dict()) for step in result.steps],
        duration_ms=result.duration_ms,
        server=CacheServerInfo.model_validate(result.server) if result.server else None,
    )
