"""Müşteri Redis sunucularının lisans kaydı.

Hub lisansın hukuki geçerliliğini doğrulamaz; Redis Server dağıtmaz. Redis hesabı tanımlayan kiracı lisans türünü
ve sahipliğini beyan eder, beyan audit'e yazılır ve bitiş tarihi izlenir.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from aih_api.errors import ApiError
from aih_api.providers.cache.capabilities import (
    COMMERCIAL_LICENSES,
    CacheLicenseStatus,
    CacheLicenseType,
    CacheProviderType,
)
from aih_api.providers.cache.models import CacheAccount
from aih_api.providers.cache.schemas import CacheLicenseIn, CacheLicenseOut
from aih_api.secrets import SecretStore

LICENSE_KEY_KIND = "cache_license_key"
EXPIRY_WARNING = timedelta(days=30)


def license_status(account: CacheAccount, today: date | None = None) -> CacheLicenseStatus:
    if account.provider_type != CacheProviderType.REDIS.value:
        return CacheLicenseStatus.NOT_REQUIRED
    if account.license_expires_on is None:
        return CacheLicenseStatus.VALID
    today = today or datetime.now(UTC).date()
    if account.license_expires_on < today:
        return CacheLicenseStatus.EXPIRED
    if account.license_expires_on - today <= EXPIRY_WARNING:
        return CacheLicenseStatus.EXPIRING
    return CacheLicenseStatus.VALID


def license_out(account: CacheAccount) -> CacheLicenseOut | None:
    if account.license_type is None:
        return None
    return CacheLicenseOut(
        type=CacheLicenseType(account.license_type),
        holder=account.license_holder,
        reference=account.license_reference,
        expires_on=account.license_expires_on,
        has_key=account.license_key_ref is not None,
        acknowledged_at=account.license_acknowledged_at,
        acknowledged_by=account.license_acknowledged_by,
    )


def _validate(payload: CacheLicenseIn, *, has_stored_key: bool) -> None:
    if not payload.acknowledged:
        raise ApiError(
            422, "AIH-CACHE-008", "Redis lisansının size ait olduğunu onaylamalısınız", "license.acknowledged"
        )
    commercial = payload.type in COMMERCIAL_LICENSES
    if commercial and not payload.holder:
        raise ApiError(422, "AIH-CACHE-009", "Ticari lisans için lisans sahibi gerekir", "license.holder")
    if payload.key is not None and not commercial:
        raise ApiError(422, "AIH-CACHE-010", "Lisans anahtarı yalnız ticari Redis lisanslarında girilir", "license.key")
    if commercial and payload.key is None and not has_stored_key:
        raise ApiError(422, "AIH-CACHE-011", "Ticari lisans için lisans anahtarı gerekir", "license.key")


def clear_license(account: CacheAccount) -> None:
    account.license_type = None
    account.license_holder = None
    account.license_reference = None
    account.license_expires_on = None
    account.license_key_ref = None
    account.license_acknowledged_at = None
    account.license_acknowledged_by = None


async def apply_license(
    session: AsyncSession, secrets: SecretStore, account: CacheAccount, payload: CacheLicenseIn | None, *, actor: str
) -> bool:
    """Lisans bilgisini uygular; Redis dışı sunucularda temizler. Beyan değiştiyse True döner."""
    if account.provider_type != CacheProviderType.REDIS.value:
        clear_license(account)
        return False
    if payload is None:
        if account.license_type is None:
            raise ApiError(422, "AIH-CACHE-007", "Redis sunucusu için lisans bilgisi gerekir", "license")
        return False
    _validate(payload, has_stored_key=account.license_key_ref is not None)
    commercial = payload.type in COMMERCIAL_LICENSES
    key = payload.key.get_secret_value() if payload.key else None
    if not commercial:
        account.license_key_ref = None
    elif key and account.license_key_ref is None:
        account.license_key_ref = await secrets.put(session, account.tenant_id, LICENSE_KEY_KIND, key)
    elif key and account.license_key_ref is not None:
        await secrets.rotate(session, account.license_key_ref, key)
    account.license_type = payload.type.value
    account.license_holder = payload.holder or None
    account.license_reference = payload.reference or None
    account.license_expires_on = payload.expires_on
    account.license_acknowledged_at = datetime.now(UTC)
    account.license_acknowledged_by = actor
    return True
