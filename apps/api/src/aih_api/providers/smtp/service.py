"""SMTP hesap iş kuralları. Tüm çağrılar tenant bağlamlı (RLS) bir oturumla yapılır."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from aih_api.audit import service as audit
from aih_api.errors import ApiError
from aih_api.identity.principal import Principal
from aih_api.providers.common import StepRecorder, decode_cursor, encode_cursor
from aih_api.providers.smtp.capabilities import (
    CAPABILITIES,
    AccountEnvironment,
    AuthMode,
    ProviderType,
    TlsMode,
)
from aih_api.providers.smtp.client import SmtpError, SmtpTarget, smtp_session
from aih_api.providers.smtp.models import SmtpAccount, SmtpConnectionTest
from aih_api.providers.smtp.network import NetworkPolicy, TargetNotAllowedError
from aih_api.providers.smtp.schemas import SmtpAccountCreate, SmtpAccountUpdate
from aih_api.secrets import SecretStore, SecretValue

SECRET_KIND = "smtp_password"  # noqa: S105 - tür etiketi, sır değil


DomainError = ApiError


@dataclass(frozen=True)
class SmtpContext:
    session: AsyncSession
    principal: Principal
    tenant_id: uuid.UUID
    secrets: SecretStore
    policy: NetworkPolicy
    platform_environment: str


SUBMISSION_PORT = 587
SMTPS_PORT = 465


def _validate_rules(ctx: SmtpContext, account: SmtpAccount, *, has_password: bool) -> None:
    _validate_capability(ctx, account)
    _validate_transport_security(ctx, account, has_password=has_password)
    try:
        ctx.policy.check_static(account.host, account.port)
    except TargetNotAllowedError as exc:
        raise DomainError(422, "AIH-SMTP-011", str(exc), "host") from exc


def _validate_capability(ctx: SmtpContext, account: SmtpAccount) -> None:
    capability = CAPABILITIES[ProviderType(account.provider_type)]
    tls = TlsMode(account.tls_mode)
    auth = AuthMode(account.auth_mode)
    env = AccountEnvironment(account.environment)

    if env not in capability.environments:
        raise DomainError(422, "AIH-SMTP-001", f"{capability.label} bu ortamda kullanılamaz", "environment")
    if ProviderType(account.provider_type) is ProviderType.MAILPIT_TEST and ctx.platform_environment in (
        "staging",
        "prod",
    ):
        raise DomainError(
            422, "AIH-SMTP-002", "Mailpit yalnız dev/test platform ortamında kullanılabilir", "providerType"
        )
    if tls not in capability.tls_modes:
        raise DomainError(422, "AIH-SMTP-003", f"{capability.label} için TLS modu desteklenmiyor", "tlsMode")
    if auth in capability.planned_auth_modes:
        raise DomainError(422, "AIH-SMTP-004", "OAuth2 bu sürümde henüz desteklenmiyor", "authMode")
    if auth not in capability.auth_modes:
        raise DomainError(
            422, "AIH-SMTP-005", f"{capability.label} için kimlik doğrulama yöntemi desteklenmiyor", "authMode"
        )


def _validate_transport_security(ctx: SmtpContext, account: SmtpAccount, *, has_password: bool) -> None:
    tls = TlsMode(account.tls_mode)
    auth = AuthMode(account.auth_mode)
    env = AccountEnvironment(account.environment)

    if tls is TlsMode.NONE and (env is AccountEnvironment.PRODUCTION or ctx.platform_environment == "prod"):
        raise DomainError(422, "AIH-SMTP-006", "Production'da TLS zorunludur", "tlsMode")
    if (
        tls is TlsMode.NONE
        and auth is AuthMode.SMTP_AUTH
        and ProviderType(account.provider_type) is not ProviderType.MAILPIT_TEST
    ):
        raise DomainError(422, "AIH-SMTP-007", "Şifre TLS olmadan gönderilemez", "tlsMode")
    if auth is AuthMode.SMTP_AUTH:
        if not account.username:
            raise DomainError(422, "AIH-SMTP-008", "SMTP AUTH için kullanıcı adı gerekir", "username")
        if not has_password:
            raise DomainError(422, "AIH-SMTP-009", "SMTP AUTH için şifre gerekir", "password")
    if tls is TlsMode.IMPLICIT and account.port == SUBMISSION_PORT:
        raise DomainError(422, "AIH-SMTP-010", "587 portu STARTTLS ile kullanılır; implicit TLS için 465", "port")
    if tls is TlsMode.STARTTLS and account.port == SMTPS_PORT:
        raise DomainError(422, "AIH-SMTP-010", "465 portu implicit TLS ile kullanılır; STARTTLS için 587", "port")


async def _name_taken(ctx: SmtpContext, name: str, exclude: uuid.UUID | None = None) -> bool:
    query = (
        select(func.count())
        .select_from(SmtpAccount)
        .where(SmtpAccount.tenant_id == ctx.tenant_id, func.lower(SmtpAccount.name) == name.lower())
    )
    if exclude is not None:
        query = query.where(SmtpAccount.id != exclude)
    return bool((await ctx.session.execute(query)).scalar_one())


async def _clear_default(ctx: SmtpContext, account: SmtpAccount) -> None:
    same_project = (
        SmtpAccount.project_id.is_(None) if account.project_id is None else SmtpAccount.project_id == account.project_id
    )
    await ctx.session.execute(
        update(SmtpAccount)
        .where(
            SmtpAccount.tenant_id == ctx.tenant_id,
            SmtpAccount.environment == account.environment,
            SmtpAccount.is_default.is_(True),
            SmtpAccount.id != account.id,
            same_project,
        )
        .values(
            is_default=False, version=SmtpAccount.version + 1, updated_at=func.now(), updated_by=ctx.principal.subject
        )
        .execution_options(synchronize_session=False)
    )


async def create(ctx: SmtpContext, payload: SmtpAccountCreate) -> SmtpAccount:
    account = SmtpAccount(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        **payload.model_dump(exclude={"password", "make_default"}),
        created_by=ctx.principal.subject,
        updated_by=ctx.principal.subject,
        is_default=False,
    )
    password = payload.password.get_secret_value() if payload.password else None
    if account.auth_mode == AuthMode.NONE.value:
        password = None
    _validate_rules(ctx, account, has_password=bool(password))
    if await _name_taken(ctx, account.name):
        raise DomainError(409, "AIH-SMTP-012", "Bu adla bir SMTP hesabı zaten var", "name")
    if password:
        account.secret_ref = await ctx.secrets.put(ctx.session, ctx.tenant_id, SECRET_KIND, password)
    ctx.session.add(account)
    await ctx.session.flush()
    if payload.make_default:
        await _make_default(ctx, account)
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.create",
        resource_type="smtp-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        details={"name": account.name, "providerType": account.provider_type, "environment": account.environment},
    )
    return account


async def get(ctx: SmtpContext, account_id: uuid.UUID) -> SmtpAccount:
    account = (
        await ctx.session.execute(
            select(SmtpAccount).where(SmtpAccount.id == account_id, SmtpAccount.tenant_id == ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if account is None:
        raise DomainError(404, "AIH-COMMON-404", "SMTP hesabı bulunamadı")
    return account


async def list_accounts(
    ctx: SmtpContext,
    *,
    environment: AccountEnvironment | None,
    enabled: bool | None,
    provider_type: ProviderType | None,
    search: str | None,
    limit: int,
    cursor: str | None,
) -> tuple[list[SmtpAccount], str | None]:
    offset = decode_cursor(cursor)
    query = select(SmtpAccount).where(SmtpAccount.tenant_id == ctx.tenant_id)
    if environment is not None:
        query = query.where(SmtpAccount.environment == environment.value)
    if enabled is not None:
        query = query.where(SmtpAccount.enabled.is_(enabled))
    if provider_type is not None:
        query = query.where(SmtpAccount.provider_type == provider_type.value)
    if search:
        pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(or_(SmtpAccount.name.ilike(pattern), SmtpAccount.sender_address.ilike(pattern)))
    query = query.order_by(
        SmtpAccount.environment, SmtpAccount.is_default.desc(), SmtpAccount.priority, SmtpAccount.name
    )
    rows = list((await ctx.session.execute(query.offset(offset).limit(limit + 1))).scalars())
    next_cursor = encode_cursor(offset + limit) if len(rows) > limit else None
    return rows[:limit], next_cursor


def _check_version(account: SmtpAccount, expected: int) -> None:
    if account.version != expected:
        raise DomainError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin")


async def update_account(
    ctx: SmtpContext, account_id: uuid.UUID, payload: SmtpAccountUpdate, expected_version: int
) -> SmtpAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(account, key, value.value if hasattr(value, "value") else value)
    if account.auth_mode == AuthMode.NONE.value and account.secret_ref is not None:
        account.secret_ref = None
    if not account.enabled:
        account.is_default = False
    _validate_rules(ctx, account, has_password=account.secret_ref is not None)
    if "name" in changes and await _name_taken(ctx, account.name, exclude=account.id):
        raise DomainError(409, "AIH-SMTP-012", "Bu adla bir SMTP hesabı zaten var", "name")
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.update",
        resource_type="smtp-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        details={"fields": sorted(changes)},
    )
    return account


async def _flush(ctx: SmtpContext) -> None:
    try:
        await ctx.session.flush()
    except StaleDataError as exc:
        raise DomainError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin") from exc


async def rotate_secret(ctx: SmtpContext, account_id: uuid.UUID, password: str, expected_version: int) -> SmtpAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    if account.auth_mode != AuthMode.SMTP_AUTH.value:
        raise DomainError(422, "AIH-SMTP-013", "Bu hesap şifre kullanmıyor", "authMode")
    if account.secret_ref is None:
        account.secret_ref = await ctx.secrets.put(ctx.session, ctx.tenant_id, SECRET_KIND, password)
    else:
        await ctx.secrets.rotate(ctx.session, account.secret_ref, password)
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.rotate-secret",
        resource_type="smtp-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
    )
    return account


async def _make_default(ctx: SmtpContext, account: SmtpAccount) -> None:
    if not account.enabled:
        raise DomainError(422, "AIH-SMTP-014", "Pasif hesap varsayılan yapılamaz", "enabled")
    await _clear_default(ctx, account)
    await ctx.session.flush()
    account.is_default = True
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)


async def make_default(ctx: SmtpContext, account_id: uuid.UUID, expected_version: int) -> SmtpAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    await _make_default(ctx, account)
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.make-default",
        resource_type="smtp-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        details={"environment": account.environment},
    )
    return account


async def resolve_secret(ctx: SmtpContext, account: SmtpAccount) -> SecretValue | None:
    if account.secret_ref is None:
        return None
    return await ctx.secrets.get(ctx.session, account.secret_ref)


def target_for(account: SmtpAccount, secret: SecretValue | None) -> SmtpTarget:
    return SmtpTarget(
        host=account.host,
        port=account.port,
        tls_mode=TlsMode(account.tls_mode),
        auth_mode=AuthMode(account.auth_mode),
        username=account.username,
        secret=secret,
        timeout=float(account.timeout_seconds),
    )


async def test_connection(ctx: SmtpContext, account_id: uuid.UUID) -> SmtpConnectionTest:
    """DNS/TCP/TLS/AUTH adımlarını dener; e-posta göndermez."""
    account = await get(ctx, account_id)
    secret = await resolve_secret(ctx, account)
    recorder = StepRecorder()
    started = time.perf_counter()
    error_code: str | None = None
    try:
        async with smtp_session(target_for(account, secret), ctx.policy, recorder):
            pass
    except SmtpError as exc:
        error_code = exc.code
    outcome = "failed" if error_code else "passed"
    result = SmtpConnectionTest(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        account_id=account.id,
        test_type="connection",
        outcome=outcome,
        error_code=error_code,
        steps=[s.as_dict() for s in recorder.steps],
        duration_ms=int((time.perf_counter() - started) * 1000),
        created_by=ctx.principal.subject,
    )
    ctx.session.add(result)
    # Bağlantı testi hesabın sürümünü değiştirmez (UI'daki düzenleme formu bayatlamasın).
    await ctx.session.execute(
        update(SmtpAccount)
        .where(SmtpAccount.id == account.id)
        .values(last_test_at=func.now(), last_test_outcome=outcome)
        .execution_options(synchronize_session=False)
    )
    await ctx.session.flush()
    await ctx.session.refresh(result)
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.test-connection",
        resource_type="smtp-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        outcome=outcome,
        details={"errorCode": error_code},
    )
    return result


async def recent_tests(ctx: SmtpContext, account_id: uuid.UUID, limit: int = 10) -> list[SmtpConnectionTest]:
    await get(ctx, account_id)
    rows = await ctx.session.execute(
        select(SmtpConnectionTest)
        .where(SmtpConnectionTest.account_id == account_id, SmtpConnectionTest.tenant_id == ctx.tenant_id)
        .order_by(SmtpConnectionTest.created_at.desc())
        .limit(limit)
    )
    return list(rows.scalars())
