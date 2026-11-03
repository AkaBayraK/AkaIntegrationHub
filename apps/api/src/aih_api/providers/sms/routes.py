from __future__ import annotations

import re
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query, Request, Response

from aih_api.db import Database
from aih_api.errors import ApiError
from aih_api.identity.deps import CurrentPrincipal, TenantScope, require
from aih_api.identity.principal import Permission
from aih_api.providers.common import mask, parse_if_match
from aih_api.providers.sms import messaging, service
from aih_api.providers.sms.capabilities import SMS_CAPABILITIES, SmsMessageStatus, SmsProviderType, SmsPurpose
from aih_api.providers.sms.models import SmsAccount, SmsMessage
from aih_api.providers.sms.schemas import (
    CreditChange,
    CreditTransactionOut,
    SendTestSms,
    SmsAccountCreate,
    SmsAccountOut,
    SmsAccountPage,
    SmsAccountUpdate,
    SmsCapabilityOut,
    SmsMessageOut,
    SmsMessagePage,
    SmsSend,
)
from aih_api.providers.sms.text import normalize_tr_mobile

router = APIRouter(prefix="/v1", tags=["sms"])
BASE = "/tenants/{tenantId}/sms-accounts"
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
TEST_BODY = "Aka Integration Hub test SMS'i. Bu mesaji beklemiyorsaniz dikkate almayin."

AccountId = Annotated[uuid.UUID, Path(alias="accountId")]
ReadScope = Annotated[TenantScope, Depends(require(Permission.SMS_ACCOUNT_READ))]
WriteScope = Annotated[TenantScope, Depends(require(Permission.SMS_ACCOUNT_WRITE))]
TestScope = Annotated[TenantScope, Depends(require(Permission.SMS_ACCOUNT_TEST))]
CreditScope = Annotated[TenantScope, Depends(require(Permission.SMS_CREDIT_MANAGE))]
SendScope = Annotated[TenantScope, Depends(require(Permission.SMS_SEND))]
MessageScope = Annotated[TenantScope, Depends(require(Permission.SMS_MESSAGE_READ))]
IfMatch = Annotated[str | None, Header(alias="If-Match")]
IdempotencyKey = Annotated[str | None, Header(alias="Idempotency-Key")]


@asynccontextmanager
async def sms_context(request: Request, scope: TenantScope) -> AsyncIterator[service.SmsContext]:
    db: Database = request.app.state.db
    async with db.transaction(scope.tenant_id) as session:
        yield service.SmsContext(
            session=session,
            principal=scope.principal,
            tenant_id=scope.tenant_id,
            secrets=request.app.state.secret_store,
            gateways=request.app.state.sms_gateways,
            platform_environment=request.app.state.settings.environment,
        )


def _out(account: SmsAccount, scope: TenantScope) -> SmsAccountOut:
    computed = {"has_secret", "low_credit"}
    fields = {name: getattr(account, name) for name in SmsAccountOut.model_fields if name not in computed}
    out = SmsAccountOut.model_validate(
        {
            **fields,
            "has_secret": account.secret_ref is not None,
            "low_credit": account.credit_balance <= account.low_credit_threshold,
        }
    )
    if not scope.principal.can(Permission.SMS_ACCOUNT_WRITE):
        out = out.model_copy(update={"username": mask(out.username)})
    return out


def _message_out(message: SmsMessage) -> SmsMessageOut:
    return SmsMessageOut.model_validate({name: getattr(message, name) for name in SmsMessageOut.model_fields})


def _etag(response: Response, account: SmsAccount) -> None:
    response.headers["ETag"] = f'W/"{account.version}"'


def _require_key(key: str | None) -> str:
    if not key or not _IDEMPOTENCY.match(key):
        raise ApiError(400, "AIH-COMMON-400", "Geçerli bir Idempotency-Key başlığı gerekli (8-128 karakter)")
    return key


@router.get("/provider-types/sms", response_model=list[SmsCapabilityOut], response_model_by_alias=True)
async def capabilities(_: CurrentPrincipal) -> list[SmsCapabilityOut]:
    return [
        SmsCapabilityOut(
            type=c.type,
            label=c.label,
            available=c.available,
            requires_credentials=c.requires_credentials,
            environments=list(c.environments),
            notes=c.notes,
        )
        for c in SMS_CAPABILITIES.values()
    ]


@router.get(BASE, response_model=SmsAccountPage, response_model_by_alias=True)
async def list_accounts(
    request: Request,
    scope: ReadScope,
    q: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> SmsAccountPage:
    async with sms_context(request, scope) as ctx:
        rows, next_cursor = await service.list_accounts(ctx, search=q, limit=limit, cursor=cursor)
        return SmsAccountPage(items=[_out(r, scope) for r in rows], next_cursor=next_cursor)


@router.post(BASE, response_model=SmsAccountOut, response_model_by_alias=True, status_code=201)
async def create_account(
    request: Request, response: Response, payload: SmsAccountCreate, scope: WriteScope
) -> SmsAccountOut:
    async with sms_context(request, scope) as ctx:
        account = await service.create(ctx, payload)
        _etag(response, account)
        response.headers["Location"] = f"/v1/tenants/{scope.tenant_id}/sms-accounts/{account.id}"
        return _out(account, scope)


@router.get(BASE + "/{accountId}", response_model=SmsAccountOut, response_model_by_alias=True)
async def get_account(request: Request, response: Response, account_id: AccountId, scope: ReadScope) -> SmsAccountOut:
    async with sms_context(request, scope) as ctx:
        account = await service.get(ctx, account_id)
        _etag(response, account)
        return _out(account, scope)


@router.patch(BASE + "/{accountId}", response_model=SmsAccountOut, response_model_by_alias=True)
async def update_account(
    request: Request,
    response: Response,
    account_id: AccountId,
    payload: SmsAccountUpdate,
    scope: WriteScope,
    if_match: IfMatch = None,
) -> SmsAccountOut:
    expected = parse_if_match(if_match)
    async with sms_context(request, scope) as ctx:
        account = await service.update_account(ctx, account_id, payload, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/make-default", response_model=SmsAccountOut, response_model_by_alias=True)
async def make_default(
    request: Request, response: Response, account_id: AccountId, scope: WriteScope, if_match: IfMatch = None
) -> SmsAccountOut:
    expected = parse_if_match(if_match)
    async with sms_context(request, scope) as ctx:
        account = await service.make_default(ctx, account_id, expected)
        _etag(response, account)
        return _out(account, scope)


@router.post(BASE + "/{accountId}/credits", response_model=SmsAccountOut, response_model_by_alias=True)
async def change_credit(
    request: Request, account_id: AccountId, payload: CreditChange, scope: CreditScope
) -> SmsAccountOut:
    async with sms_context(request, scope) as ctx:
        return _out(await service.apply_credit(ctx, account_id, payload), scope)


@router.get(BASE + "/{accountId}/credits", response_model=list[CreditTransactionOut], response_model_by_alias=True)
async def credit_history(request: Request, account_id: AccountId, scope: ReadScope) -> list[CreditTransactionOut]:
    async with sms_context(request, scope) as ctx:
        rows = await service.credit_history(ctx, account_id)
        return [
            CreditTransactionOut.model_validate({n: getattr(r, n) for n in CreditTransactionOut.model_fields})
            for r in rows
        ]


async def _dispatch(
    request: Request, scope: TenantScope, account_id: uuid.UUID | None, req: messaging.SendRequest, key: str
) -> SmsMessageOut:
    async with sms_context(request, scope) as ctx:
        account = await service.get(ctx, account_id) if account_id else None
        if account is None:
            raise ApiError(422, "AIH-SMS-007", "SMS hesabı belirtilmeli", "accountId")
        pending = await messaging.begin_send(ctx, account, req, key)
    if isinstance(pending, SmsMessage):
        return _message_out(pending)
    gateway = request.app.state.sms_gateways[pending.provider_type]
    started = time.perf_counter()
    result = await gateway.send(pending.request)
    duration = int((time.perf_counter() - started) * 1000)
    async with sms_context(request, scope) as ctx:
        return _message_out(await messaging.finish_send(ctx, pending.message_id, result, duration))


@router.post(BASE + "/{accountId}/send-test", response_model=SmsMessageOut, response_model_by_alias=True)
async def send_test(
    request: Request,
    account_id: AccountId,
    payload: SendTestSms,
    scope: TestScope,
    idempotency_key: IdempotencyKey = None,
) -> SmsMessageOut:
    key = _require_key(idempotency_key)
    if not payload.confirm:
        raise ApiError(422, "AIH-SMS-017", "Test SMS'i gönderimi onaylanmalıdır", "confirm")
    async with sms_context(request, scope) as ctx:
        account = await service.get(ctx, account_id)
        provider = account.provider_type
    allowlist = {
        normalize_tr_mobile(p) for p in request.app.state.settings.sms_test_recipient_allowlist.split(",") if p.strip()
    }
    if provider != SmsProviderType.MOCK_TEST.value and normalize_tr_mobile(payload.phone) not in allowlist:
        raise ApiError(422, "AIH-SMS-018", "Gerçek sağlayıcıyla test SMS'i yalnız izinli numaralara gider", "phone")
    req = messaging.SendRequest(payload.phone, TEST_BODY, SmsPurpose.TRANSACTIONAL, kind="test", type_code="HUB_TEST")
    return await _dispatch(request, scope, account_id, req, key)


@router.post("/tenants/{tenantId}/sms/messages", response_model=SmsMessageOut, response_model_by_alias=True)
async def send_sms(
    request: Request, payload: SmsSend, scope: SendScope, idempotency_key: IdempotencyKey = None
) -> SmsMessageOut:
    key = _require_key(idempotency_key)
    account_id = payload.account_id
    if account_id is None:
        async with sms_context(request, scope) as ctx:
            account_id = (await service.default_account(ctx, payload.environment)).id
    req = messaging.SendRequest(
        phone=payload.phone,
        body=payload.body,
        purpose=payload.purpose,
        type_code=payload.type_code,
        reference_type=payload.reference.type if payload.reference else None,
        reference_id=payload.reference.id if payload.reference else None,
        consent_reference=payload.consent_reference,
    )
    return await _dispatch(request, scope, account_id, req, key)


@router.get("/tenants/{tenantId}/sms/messages", response_model=SmsMessagePage, response_model_by_alias=True)
async def list_messages(
    request: Request,
    scope: MessageScope,
    account_id: Annotated[uuid.UUID | None, Query(alias="accountId")] = None,
    status: SmsMessageStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    cursor: str | None = None,
) -> SmsMessagePage:
    async with sms_context(request, scope) as ctx:
        rows, next_cursor = await messaging.list_messages(
            ctx, account_id=account_id, status=status, limit=limit, cursor=cursor
        )
        return SmsMessagePage(items=[_message_out(r) for r in rows], next_cursor=next_cursor)
