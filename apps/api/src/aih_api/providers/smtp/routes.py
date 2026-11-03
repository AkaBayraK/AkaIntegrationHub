from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from aih_api.db import Database
from aih_api.identity.deps import CurrentPrincipal, TenantScope, require
from aih_api.identity.principal import Permission
from aih_api.providers.common import mask, parse_if_match
from aih_api.providers.smtp import service
from aih_api.providers.smtp.capabilities import CAPABILITIES, AccountEnvironment, ProviderType
from aih_api.providers.smtp.models import SmtpAccount
from aih_api.providers.smtp.schemas import (
    CapabilityOut,
    ConnectionTestOut,
    SecretRotate,
    SmtpAccountCreate,
    SmtpAccountOut,
    SmtpAccountPage,
    SmtpAccountUpdate,
)

router = APIRouter(prefix="/v1", tags=["smtp"])
BASE = "/tenants/{tenantId}/smtp-accounts"


@asynccontextmanager
async def smtp_context(request: Request, scope: TenantScope) -> AsyncIterator[service.SmtpContext]:
    db: Database = request.app.state.db
    async with db.transaction(scope.tenant_id) as session:
        yield service.SmtpContext(
            session=session,
            principal=scope.principal,
            tenant_id=scope.tenant_id,
            secrets=request.app.state.secret_store,
            policy=request.app.state.smtp_policy,
            platform_environment=request.app.state.settings.environment,
        )


def _out(account: SmtpAccount, scope: TenantScope) -> SmtpAccountOut:
    data = {name: getattr(account, name, None) for name in SmtpAccountOut.model_fields if name != "has_secret"}
    out = SmtpAccountOut.model_validate({**data, "has_secret": account.secret_ref is not None})
    if not scope.principal.can(Permission.SMTP_ACCOUNT_WRITE):
        # Viewer: bağlantı/kimlik ayrıntıları maskelenir.
        out = out.model_copy(update={"host": mask(out.host) or "", "username": mask(out.username)})
    return out


def _etag(response: Response, account: SmtpAccount) -> None:
    response.headers["ETag"] = f'W/"{account.version}"'


IfMatch = Annotated[str | None, Header(alias="If-Match")]


@router.get("/provider-types/smtp", response_model=list[CapabilityOut], response_model_by_alias=True)
async def capabilities(_: CurrentPrincipal) -> list[CapabilityOut]:
    return [
        CapabilityOut(
            type=c.type,
            label=c.label,
            default_host=c.default_host,
            default_port=c.default_port,
            default_tls=c.default_tls,
            tls_modes=list(c.tls_modes),
            auth_modes=list(c.auth_modes),
            planned_auth_modes=list(c.planned_auth_modes),
            environments=list(c.environments),
            notes=c.notes,
        )
        for c in CAPABILITIES.values()
    ]


@router.get(BASE, response_model=SmtpAccountPage, response_model_by_alias=True)
async def list_accounts(
    request: Request,
    scope: Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_READ))],
    environment: AccountEnvironment | None = None,
    enabled: bool | None = None,
    provider_type: Annotated[ProviderType | None, Query(alias="providerType")] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> SmtpAccountPage:
    async with smtp_context(request, scope) as ctx:
        rows, next_cursor = await service.list_accounts(
            ctx,
            environment=environment,
            enabled=enabled,
            provider_type=provider_type,
            search=q,
            limit=limit,
            cursor=cursor,
        )
        return SmtpAccountPage(items=[_out(r, scope) for r in rows], next_cursor=next_cursor)


@router.post(BASE, response_model=SmtpAccountOut, response_model_by_alias=True, status_code=201)
async def create_account(
    request: Request,
    response: Response,
    payload: SmtpAccountCreate,
    scope: Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_WRITE))],
) -> SmtpAccountOut:
    async with smtp_context(request, scope) as ctx:
        account = await service.create(ctx, payload)
        _etag(response, account)
        response.headers["Location"] = f"/v1/tenants/{scope.tenant_id}/smtp-accounts/{account.id}"
        return _out(account, scope)


AccountId = Annotated[uuid.UUID, Path(alias="accountId")]
ReadScope = Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_READ))]
WriteScope = Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_WRITE))]
TestScope = Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_TEST))]


@router.get(BASE + "/{accountId}", response_model=SmtpAccountOut, response_model_by_alias=True)
async def get_account(request: Request, response: Response, account_id: AccountId, scope: ReadScope) -> SmtpAccountOut:
    async with smtp_context(request, scope) as ctx:
        account = await service.get(ctx, account_id)
        _etag(response, account)
        return _out(account, scope)


@router.patch(BASE + "/{accountId}", response_model=SmtpAccountOut, response_model_by_alias=True)
async def update_account(
    request: Request,
    response: Response,
    account_id: AccountId,
    payload: SmtpAccountUpdate,
    scope: WriteScope,
    if_match: IfMatch = None,
) -> SmtpAccountOut:
    expected = parse_if_match(if_match)
    async with smtp_context(request, scope) as ctx:
        account = await service.update_account(ctx, account_id, payload, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/secret", response_model=SmtpAccountOut, response_model_by_alias=True)
async def rotate_secret(
    request: Request,
    response: Response,
    account_id: AccountId,
    payload: SecretRotate,
    scope: WriteScope,
    if_match: IfMatch = None,
) -> SmtpAccountOut:
    expected = parse_if_match(if_match)
    async with smtp_context(request, scope) as ctx:
        account = await service.rotate_secret(ctx, account_id, payload.password.get_secret_value(), expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/make-default", response_model=SmtpAccountOut, response_model_by_alias=True)
async def make_default(
    request: Request, response: Response, account_id: AccountId, scope: WriteScope, if_match: IfMatch = None
) -> SmtpAccountOut:
    expected = parse_if_match(if_match)
    async with smtp_context(request, scope) as ctx:
        account = await service.make_default(ctx, account_id, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/test-connection", response_model=ConnectionTestOut, response_model_by_alias=True)
async def test_connection(request: Request, account_id: AccountId, scope: TestScope) -> ConnectionTestOut:
    async with smtp_context(request, scope) as ctx:
        return ConnectionTestOut.from_row(await service.test_connection(ctx, account_id))


@router.get(
    BASE + "/{accountId}/connection-tests", response_model=list[ConnectionTestOut], response_model_by_alias=True
)
async def connection_tests(request: Request, account_id: AccountId, scope: ReadScope) -> list[ConnectionTestOut]:
    async with smtp_context(request, scope) as ctx:
        return [ConnectionTestOut.from_row(r) for r in await service.recent_tests(ctx, account_id)]
