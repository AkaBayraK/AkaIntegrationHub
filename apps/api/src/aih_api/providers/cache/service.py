"""Cache hesap iş kuralları. Tüm çağrılar tenant bağlamlı (RLS) bir oturumla yapılır."""

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
from aih_api.providers.cache.capabilities import CacheAuthMode, CacheEnvironment
from aih_api.providers.cache.client import CacheError, CacheTarget, cache_session, server_info
from aih_api.providers.cache.models import CacheAccount
from aih_api.providers.cache.schemas import CacheAccountCreate, CacheAccountUpdate
from aih_api.providers.common import Step, StepRecorder, decode_cursor, encode_cursor
from aih_api.providers.smtp.network import NetworkPolicy, TargetNotAllowedError
from aih_api.secrets import SecretStore

SECRET_KIND = "cache_password"  # noqa: S105 - tür etiketi, sır değil
MAX_VERSION_LENGTH = 64


@dataclass(frozen=True)
class CacheContext:
    session: AsyncSession
    principal: Principal
    tenant_id: uuid.UUID
    secrets: SecretStore
    policy: NetworkPolicy


@dataclass(frozen=True)
class ConnectionTestResult:
    account_id: uuid.UUID
    outcome: str
    error_code: str | None
    steps: list[Step]
    duration_ms: int
    server: dict[str, object] | None


def _validate(ctx: CacheContext, account: CacheAccount, *, has_password: bool) -> None:
    auth = CacheAuthMode(account.auth_mode)
    if auth is CacheAuthMode.NONE and account.environment == CacheEnvironment.PRODUCTION.value:
        raise ApiError(422, "AIH-CACHE-001", "Production hesabında kimlik doğrulama zorunludur", "authMode")
    if auth is CacheAuthMode.ACL and not account.username:
        raise ApiError(422, "AIH-CACHE-002", "ACL kimlik doğrulaması için kullanıcı adı gerekir", "username")
    if auth is not CacheAuthMode.NONE and not has_password:
        raise ApiError(422, "AIH-CACHE-003", "Kimlik doğrulaması için şifre gerekir", "password")
    try:
        ctx.policy.check_static(account.host, account.port)
    except TargetNotAllowedError as exc:
        raise ApiError(422, "AIH-CACHE-004", str(exc), "host") from exc


async def _name_taken(ctx: CacheContext, name: str, exclude: uuid.UUID | None = None) -> bool:
    query = (
        select(func.count())
        .select_from(CacheAccount)
        .where(CacheAccount.tenant_id == ctx.tenant_id, func.lower(CacheAccount.name) == name.lower())
    )
    if exclude is not None:
        query = query.where(CacheAccount.id != exclude)
    return bool((await ctx.session.execute(query)).scalar_one())


async def _audit(ctx: CacheContext, action: str, account: CacheAccount, **details: object) -> None:
    await audit.record(
        ctx.session,
        ctx.principal,
        action=f"cache-account.{action}",
        resource_type="cache-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        details=dict(details),
    )


async def _store_password(ctx: CacheContext, account: CacheAccount, password: str | None) -> None:
    if account.auth_mode == CacheAuthMode.NONE.value:
        account.secret_ref = None
    elif password and account.secret_ref is None:
        account.secret_ref = await ctx.secrets.put(ctx.session, ctx.tenant_id, SECRET_KIND, password)
    elif password and account.secret_ref is not None:
        await ctx.secrets.rotate(ctx.session, account.secret_ref, password)


async def create(ctx: CacheContext, payload: CacheAccountCreate) -> CacheAccount:
    account = CacheAccount(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        **payload.model_dump(exclude={"password", "make_default"}),
        is_default=False,
        created_by=ctx.principal.subject,
        updated_by=ctx.principal.subject,
    )
    password = payload.password.get_secret_value() if payload.password else None
    _validate(ctx, account, has_password=bool(password))
    if await _name_taken(ctx, account.name):
        raise ApiError(409, "AIH-CACHE-005", "Bu adla bir cache hesabı zaten var", "name")
    await _store_password(ctx, account, password)
    ctx.session.add(account)
    await ctx.session.flush()
    if payload.make_default:
        await _make_default(ctx, account)
    await _audit(ctx, "create", account, name=account.name, providerType=account.provider_type)
    return account


async def get(ctx: CacheContext, account_id: uuid.UUID) -> CacheAccount:
    account = (
        await ctx.session.execute(
            select(CacheAccount).where(CacheAccount.id == account_id, CacheAccount.tenant_id == ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if account is None:
        raise ApiError(404, "AIH-COMMON-404", "Cache hesabı bulunamadı")
    return account


async def list_accounts(
    ctx: CacheContext, *, search: str | None, limit: int, cursor: str | None
) -> tuple[list[CacheAccount], str | None]:
    offset = decode_cursor(cursor)
    query = select(CacheAccount).where(CacheAccount.tenant_id == ctx.tenant_id)
    if search:
        pattern = "%" + search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
        query = query.where(or_(CacheAccount.name.ilike(pattern), CacheAccount.host.ilike(pattern)))
    query = query.order_by(CacheAccount.environment, CacheAccount.is_default.desc(), CacheAccount.name)
    rows = list((await ctx.session.execute(query.offset(offset).limit(limit + 1))).scalars())
    return rows[:limit], encode_cursor(offset + limit) if len(rows) > limit else None


def _check_version(account: CacheAccount, expected: int) -> None:
    if account.version != expected:
        raise ApiError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin")


async def _flush(ctx: CacheContext) -> None:
    try:
        await ctx.session.flush()
    except StaleDataError as exc:
        raise ApiError(412, "AIH-COMMON-412", "Kayıt başka biri tarafından değiştirildi; yeniden yükleyin") from exc


async def update_account(
    ctx: CacheContext, account_id: uuid.UUID, payload: CacheAccountUpdate, expected_version: int
) -> CacheAccount:
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
        raise ApiError(409, "AIH-CACHE-005", "Bu adla bir cache hesabı zaten var", "name")
    await _store_password(ctx, account, password)
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)
    await _audit(ctx, "update", account, fields=sorted([*changes, *(["password"] if password else [])]))
    return account


async def _make_default(ctx: CacheContext, account: CacheAccount) -> None:
    if not account.enabled:
        raise ApiError(422, "AIH-CACHE-006", "Pasif hesap varsayılan yapılamaz", "enabled")
    same_project = (
        CacheAccount.project_id.is_(None)
        if account.project_id is None
        else CacheAccount.project_id == account.project_id
    )
    await ctx.session.execute(
        update(CacheAccount)
        .where(
            CacheAccount.tenant_id == ctx.tenant_id,
            CacheAccount.environment == account.environment,
            CacheAccount.is_default.is_(True),
            CacheAccount.id != account.id,
            same_project,
        )
        .values(is_default=False, version=CacheAccount.version + 1, updated_by=ctx.principal.subject)
        .execution_options(synchronize_session=False)
    )
    await ctx.session.flush()
    account.is_default = True
    account.updated_by = ctx.principal.subject
    account.updated_at = datetime.now(UTC)
    await _flush(ctx)


async def make_default(ctx: CacheContext, account_id: uuid.UUID, expected_version: int) -> CacheAccount:
    account = await get(ctx, account_id)
    _check_version(account, expected_version)
    await _make_default(ctx, account)
    await _audit(ctx, "make-default", account, environment=account.environment)
    return account


async def _target(ctx: CacheContext, account: CacheAccount) -> CacheTarget:
    secret = await ctx.secrets.get(ctx.session, account.secret_ref) if account.secret_ref else None
    return CacheTarget(
        host=account.host,
        port=account.port,
        tls=account.tls_enabled,
        auth_mode=CacheAuthMode(account.auth_mode),
        username=account.username,
        secret=secret,
        database=account.database_index,
        timeout=float(account.timeout_seconds),
    )


async def test_connection(ctx: CacheContext, account_id: uuid.UUID) -> ConnectionTestResult:
    """DNS/TCP/TLS/AUTH/SELECT/PING adımlarını dener ve sunucu özetini okur; veri yazmaz."""
    account = await get(ctx, account_id)
    target = await _target(ctx, account)
    recorder = StepRecorder()
    started = time.perf_counter()
    error_code: str | None = None
    info: dict[str, object] | None = None
    try:
        async with cache_session(target, ctx.policy, recorder) as conn, recorder.step("info"):
            info = await server_info(conn)
    except CacheError as exc:
        error_code = exc.code
    outcome = "failed" if error_code else "passed"
    version = str(info.get("version"))[:MAX_VERSION_LENGTH] if info and info.get("version") else None
    # Bağlantı testi hesabın sürümünü değiştirmez (UI'daki düzenleme formu bayatlamasın).
    await ctx.session.execute(
        update(CacheAccount)
        .where(CacheAccount.id == account.id)
        .values(
            last_test_at=func.now(),
            last_test_outcome=outcome,
            server_version=version or CacheAccount.server_version,
        )
        .execution_options(synchronize_session=False)
    )
    await audit.record(
        ctx.session,
        ctx.principal,
        action="cache-account.test-connection",
        resource_type="cache-account",
        resource_id=account.id,
        tenant_id=ctx.tenant_id,
        outcome=outcome,
        details={"errorCode": error_code},
    )
    return ConnectionTestResult(
        account_id=account.id,
        outcome=outcome,
        error_code=error_code,
        steps=recorder.steps,
        duration_ms=int((time.perf_counter() - started) * 1000),
        server=info,
    )
