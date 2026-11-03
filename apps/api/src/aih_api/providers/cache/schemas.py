from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr, field_validator

from aih_api.providers.cache.capabilities import CacheAuthMode, CacheEnvironment, CacheProviderType
from aih_api.providers.common import ApiModel, ConsoleUrl, strip_single_line

MAX_DATABASE_INDEX = 15
_KEY_PREFIX = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")


def _key_prefix(value: str) -> str:
    if not _KEY_PREFIX.match(value):
        raise ValueError("yalnız harf, rakam ve . _ : - içerebilir")
    return value


KeyPrefix = Annotated[str, AfterValidator(_key_prefix)]


class CacheCapabilityOut(ApiModel):
    type: CacheProviderType
    label: str
    default_port: int
    license_note: str


class CacheAccountCreate(ApiModel):
    project_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    provider_type: CacheProviderType = CacheProviderType.VALKEY
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(default=6379, ge=1, le=65535)
    tls_enabled: bool = False
    auth_mode: CacheAuthMode = CacheAuthMode.NONE
    username: str | None = Field(default=None, max_length=255)
    # Yalnız yazılır, asla okunmaz.
    password: SecretStr | None = Field(default=None, max_length=1024)
    database_index: int = Field(default=0, ge=0, le=MAX_DATABASE_INDEX)
    key_prefix: KeyPrefix | None = None
    environment: CacheEnvironment
    enabled: bool = True
    make_default: bool = False
    timeout_seconds: int = Field(default=5, ge=1, le=60)
    console_url: ConsoleUrl | None = None

    _strip = field_validator("name", "host", "username")(strip_single_line)


class CacheAccountUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    host: str | None = Field(default=None, min_length=1, max_length=253)
    port: int | None = Field(default=None, ge=1, le=65535)
    tls_enabled: bool | None = None
    auth_mode: CacheAuthMode | None = None
    username: str | None = Field(default=None, max_length=255)
    password: SecretStr | None = Field(default=None, max_length=1024)
    database_index: int | None = Field(default=None, ge=0, le=MAX_DATABASE_INDEX)
    key_prefix: KeyPrefix | None = None
    environment: CacheEnvironment | None = None
    enabled: bool | None = None
    timeout_seconds: int | None = Field(default=None, ge=1, le=60)
    console_url: ConsoleUrl | None = None

    _strip = field_validator("name", "host", "username")(strip_single_line)


class CacheAccountOut(ApiModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    provider_type: CacheProviderType
    host: str
    port: int
    tls_enabled: bool
    auth_mode: CacheAuthMode
    username: str | None
    has_secret: bool
    database_index: int
    key_prefix: str | None
    environment: CacheEnvironment
    enabled: bool
    is_default: bool
    timeout_seconds: int
    console_url: str | None
    last_test_at: datetime | None
    last_test_outcome: str | None
    server_version: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class CacheAccountPage(ApiModel):
    items: list[CacheAccountOut]
    next_cursor: str | None


class CacheTestStep(ApiModel):
    step: str
    outcome: str
    duration_ms: int
    error_code: str | None


class CacheServerInfo(ApiModel):
    server_name: str | None = None
    version: str | None = None
    mode: str | None = None
    role: str | None = None
    uptime_seconds: int | None = None
    connected_clients: int | None = None
    used_memory: str | None = None
    max_memory: str | None = None
    eviction_policy: str | None = None
    keyspace: dict[str, int] = Field(default_factory=dict)


class CacheConnectionTestOut(ApiModel):
    account_id: uuid.UUID
    outcome: str
    error_code: str | None
    steps: list[CacheTestStep]
    duration_ms: int
    server: CacheServerInfo | None
