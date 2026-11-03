"""SMS hesap ve kontör iş kuralları. Tüm çağrılar tenant bağlamlı (RLS) bir oturumla yapılır."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from aih_api.audit import service as audit
from aih_api.errors import ApiError
from aih_api.identity.principal import Principal
from aih_api.providers.common import decode_cursor, encode_cursor
from aih_api.providers.sms.capabilities import SMS_CAPABILITIES, SmsCreditType, SmsEnvironment, SmsProviderType
from aih_api.providers.sms.gateways import SmsGateway
from aih_api.providers.sms.models import SmsAccount, SmsCreditTransaction
from aih_api.providers.sms.schemas import MAX_CREDIT, CreditChange, SmsAccountCreate, SmsAccountUpdate
from aih_api.secrets import SecretStore

SECRET_KIND = "sms_password"  # noqa: S105 - tür etiketi, sır değil
PRODUCTION_PLATFORMS = ("staging", "prod")


@dataclass(frozen=True)
class SmsContext:
    session: AsyncSession
    principal: Principal
    tenant_id: uuid.UUID
    secrets: SecretStore
    gateways: dict[SmsProviderType, SmsGateway]
    platform_environment: str


def _validate(ctx: SmsContext, account: SmsAccount, *, has_password: bool) -> None:
    capability = SMS_CAPABILITIES[SmsProviderType(account.provider_type)]
    if not capability.available or SmsProviderType(account.provider_type) not in ctx.gateways:
        raise ApiError(422, "AIH-SMS-001", f"{capability.label} adaptörü henüz hazır değil", "providerType")
    if SmsEnvironment(account.environment) not in capability.environments:
        raise ApiError(422, "AIH-SMS-002", f"{capability.label} bu ortamda kullanılamaz", "environment")
    if account.provider_type == SmsProviderType.MOCK_TEST.value and ctx.platform_environment in PRODUCTION_PLATFORMS:
        raise ApiError(
            422, "AIH-SMS-003", "Test sağlayıcısı yalnız dev/test platformunda kullanılabilir", "providerType"
        )
    if capability.requires_credentials and not account.username:
        raise ApiError(422, "AIH-SMS-004", f"{capability.label} için kullanıcı kodu gerekir", "username")
    if capability.requires_credentials and not has_password:
        raise ApiError(422, "AIH-SMS-005", f"{capability.label} için API şifresi gerekir", "password")


async def _name_taken(ctx: SmsContext, name: str, exclude: uuid.UUID | None = None) -> bool:
    query = (
        select(func.count())
        .select_from(SmsAccount)
        .where(SmsAccount.tenant_id == ctx.tenant_id, func.lower(SmsAccount.name) == name.lower())
    )
    if exclude is not None:
        query = query.where(SmsAccount.id != exclude)
    return bool((await ctx.session.execute(query)).scalar_one())


async def _audit(ctx: SmsContext, action: str, account: SmsAccount, **details: object) -> None:
    await audit.record(
        ctx.session,
        ctx.principal,
        action=f"sms-account.{action}",
        resource_type="sms-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        details=dict(details),
    )


async def _store_password(ctx: SmsContext, account: SmsAccount, password: str | None) -> None:
    if not SMS_CAPABILITIES[SmsProviderType(account.provider_type)].requires_credentials:
        account.secret_ref = None
    elif password and account.secret_ref is None:
        account.secret_ref = await ctx.secrets.put(ctx.session, ctx.tenant_id, SECRET_KIND, password)
    elif password and account.secret_ref is not None:
        await ctx.secrets.rotate(ctx.session, account.secret_ref, password)


async def create(ctx: SmsContext, payload: SmsAccountCreate) -> SmsAccount:
    account = SmsAccount(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        **payload.model_dump(exclude={"password", "make_default"}),
        is_default=False,
        credit_balance=0,
        created_by=ctx.principal.subject,
        updated_by=ctx.principal.subject,
    )
    password = payload.password.get_secret_value() if payload.password else None
    _validate(ctx, account, has_password=bool(password))
    if await _name_taken(ctx, account.name):
        raise ApiError(409, "AIH-SMS-006", "Bu adla bir SMS hesabı zaten var", "name")
    await _store_password(ctx, account, password)
    ctx.session.add(account)
    await ctx.session.flush()
    if payload.make_default:
        await _make_default(ctx, account)
    await _audit(ctx, "create", account, name=account.name, providerType=account.provider_type)
    return account


async def get(ctx: SmsContext, account_id: uuid.UUID) -> SmsAccount:
    account = (
        await ctx.session.execute(
            select(SmsAccount)
            .where(SmsAccount.id == account_id, SmsAccount.tenant_id == ctx.tenant_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if account is None:
        raise ApiError(404, "AIH-COMMON-404", "SMS hesabı bulunamadı")
    return account


async def default_account(ctx: SmsContext, environment: SmsEnvironment) -> SmsAccount:
    account = (
        await ctx.session.execute(
            select(SmsAccount).where(
                SmsAccount.tenant_id == ctx.tenant_id,
                SmsAccount.environment == environment.value,
                SmsAccount.is_default.is_(True),
                SmsAccount.project_id.is_(None),
            )
        )
    ).scalar_one_or_none()
    if account is None:
        raise ApiError(422, "AIH-SMS-007", "Bu ortam için varsayılan SMS hesabı tanımlı değil", "accountId")
    return account


async def list_accounts(
    ctx: SmsContext, *, search: str | None, limit: int, cursor: str | None
) -> tuple[list[SmsAccount], str | None]:
    offset = decode_cursor(cursor)
    query = select(SmsAccount).where(SmsAccount.tenant_id == ctx.tenant_id)
    if search:
        pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(or_(SmsAccount.name.ilike(pattern), SmsAccount.sender_header.ilike(pattern)))
    query = query.order_by(SmsAccount.environment, SmsAccount.is_default.desc(), SmsAccount.name)
    rows = list((await ctx.session.execute(query.offset(offset).limit(limit + 1))).scalars())
    return rows[:limit], encode_cursor(offset + limit) if len(rows) > limit else None


async def _flush(ctx: SmsContext) -> None:
    try:
        await ctx.session.flush()
    except StaleDataError as exc:
        raise ApiError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin") from exc


def _check_version(account: SmsAccount, expected: int) -> None:
    if account.version != expected:
        raise ApiError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin")


async def update_account(
    ctx: SmsContext, account_id: uuid.UUID, payload: SmsAccountUpdate, expected_version: int
) -> SmsAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    changes = payload.model_dump(exclude_unset=True, exclude={"password"})
    for key, value in changes.items():
        setattr(account, key, value.value if hasattr(value, "value") else value)
    password = payload.password.get_secret_value() if payload.password else None
    if not account.enabled:
        account.is_default = False
    _validate(ctx, account, has_password=bool(password) or account.secret_ref is not None)
    if "name" in changes and await _name_taken(ctx, account.name, exclude=account.id):
        raise ApiError(409, "AIH-SMS-006", "Bu adla bir SMS hesabı zaten var", "name")
    await _store_password(ctx, account, password)
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)
    await _audit(ctx, "update", account, fields=sorted([*changes, *(["password"] if password else [])]))
    return account


async def _make_default(ctx: SmsContext, account: SmsAccount) -> None:
    if not account.enabled:
        raise ApiError(422, "AIH-SMS-008", "Pasif hesap varsayılan yapılamaz", "enabled")
    same_project = (
        SmsAccount.project_id.is_(None) if account.project_id is None else SmsAccount.project_id == account.project_id
    )
    await ctx.session.execute(
        update(SmsAccount)
        .where(
            SmsAccount.tenant_id == ctx.tenant_id,
            SmsAccount.environment == account.environment,
            SmsAccount.is_default.is_(True),
            SmsAccount.id != account.id,
            same_project,
        )
        .values(is_default=False, version=SmsAccount.version + 1, updated_by=ctx.principal.subject)
        .execution_options(synchronize_session=False)
    )
    await ctx.session.flush()
    account.is_default = True
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)


async def make_default(ctx: SmsContext, account_id: uuid.UUID, expected_version: int) -> SmsAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    await _make_default(ctx, account)
    await _audit(ctx, "make-default", account, environment=account.environment)
    return account


async def change_balance(
    ctx: SmsContext,
    account: SmsAccount,
    delta: int,
    *,
    kind: SmsCreditType,
    reason: str | None = None,
    message_id: uuid.UUID | None = None,
) -> int | None:
    """Bakiyeyi tek atomik SQL ile değiştirir; bakiye eksiye ya da üst sınırın üstüne çıkacaksa None döner."""
    balance = (
        await ctx.session.execute(
            text(
                "UPDATE provider.sms_accounts SET credit_balance = credit_balance + :delta "
                "WHERE id = :id AND credit_balance + :delta BETWEEN 0 AND :max RETURNING credit_balance"
            ),
            {"delta": delta, "id": account.id, "max": MAX_CREDIT},
        )
    ).scalar_one_or_none()
    if balance is None:
        return None
    ctx.session.add(
        SmsCreditTransaction(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            account_id=account.id,
            kind=kind.value,
            quantity=delta,
            balance_after=int(balance),
            reason=reason,
            message_id=message_id,
            created_by=ctx.principal.subject,
        )
    )
    await ctx.session.flush()
    return int(balance)


async def apply_credit(ctx: SmsContext, account_id: uuid.UUID, payload: CreditChange) -> SmsAccount:
    account = await get(ctx, account_id)
    if payload.kind not in (SmsCreditType.LOAD, SmsCreditType.ADJUST):
        raise ApiError(422, "AIH-SMS-009", "Yalnız kontör yükleme veya düzeltme yapılabilir", "kind")
    if payload.quantity == 0 or (payload.kind is SmsCreditType.LOAD and payload.quantity < 0):
        raise ApiError(422, "AIH-SMS-010", "Yükleme miktarı pozitif olmalı", "quantity")
    balance = await change_balance(ctx, account, payload.quantity, kind=payload.kind, reason=payload.reason)
    if balance is None:
        raise ApiError(422, "AIH-SMS-011", "Bakiye sıfırın altına ya da üst sınırın üstüne çıkamaz", "quantity")
    await _audit(ctx, "credit", account, kind=payload.kind.value, quantity=payload.quantity, balance=balance)
    return await get(ctx, account_id)


async def credit_history(ctx: SmsContext, account_id: uuid.UUID, limit: int = 50) -> list[SmsCreditTransaction]:
    await get(ctx, account_id)
    rows = await ctx.session.execute(
        select(SmsCreditTransaction)
        .where(SmsCreditTransaction.account_id == account_id, SmsCreditTransaction.tenant_id == ctx.tenant_id)
        .order_by(SmsCreditTransaction.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars())


async def record_test(ctx: SmsContext, account: SmsAccount, outcome: str, error_code: str | None) -> None:
    await ctx.session.execute(
        update(SmsAccount)
        .where(SmsAccount.id == account.id)
        .values(last_test_at=func.now(), last_test_outcome=outcome)
        .execution_options(synchronize_session=False)
    )
    await audit.record(
        ctx.session,
        ctx.principal,
        action="sms-account.test",
        resource_type="sms-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        outcome=outcome,
        details={"errorCode": error_code},
    )
