"""Cache sağlayıcı türleri ve yetenekleri (RESP protokolü konuşan sunucular)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CacheProviderType(StrEnum):
    VALKEY = "valkey"
    REDIS = "redis"


class CacheAuthMode(StrEnum):
    NONE = "none"
    PASSWORD = "password"  # noqa: S105 - kimlik doğrulama türü adı, sır değil
    ACL = "acl"


class CacheEnvironment(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class CacheCapability:
    type: CacheProviderType
    label: str
    default_port: int
    license_note: str


CACHE_CAPABILITIES: dict[CacheProviderType, CacheCapability] = {
    c.type: c
    for c in (
        CacheCapability(
            CacheProviderType.VALKEY,
            "Valkey",
            6379,
            "BSD-3-Clause. Hub'ın varsayılan ve önerilen cache sunucusu.",
        ),
        CacheCapability(
            CacheProviderType.REDIS,
            "Redis (müşteri sunucusu)",
            6379,
            "Redis 7.4+ RSALv2/SSPLv1/AGPLv3 lisanslıdır; sunucunun lisansı sahibinin sorumluluğundadır.",
        ),
    )
}
