from __future__ import annotations

from datetime import date

import pytest

from aih_api.providers.cache.capabilities import CacheLicenseStatus
from aih_api.providers.cache.license import license_status
from aih_api.providers.cache.models import CacheAccount

TODAY = date(2026, 11, 3)


@pytest.mark.parametrize(
    ("provider", "expires_on", "expected"),
    [
        ("valkey", None, CacheLicenseStatus.NOT_REQUIRED),
        ("redis", None, CacheLicenseStatus.VALID),
        ("redis", date(2027, 6, 1), CacheLicenseStatus.VALID),
        ("redis", date(2026, 12, 3), CacheLicenseStatus.EXPIRING),
        ("redis", TODAY, CacheLicenseStatus.EXPIRING),
        ("redis", date(2026, 11, 2), CacheLicenseStatus.EXPIRED),
    ],
)
def test_license_status(provider: str, expires_on: date | None, expected: CacheLicenseStatus) -> None:
    account = CacheAccount(provider_type=provider, license_expires_on=expires_on)

    assert license_status(account, TODAY) is expected
