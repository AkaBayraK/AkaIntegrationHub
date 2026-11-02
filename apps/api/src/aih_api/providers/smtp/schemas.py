from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic.alias_generators import to_camel

from aih_api.providers.smtp.capabilities import AccountEnvironment, AuthMode, ProviderType, TlsMode

_EMAIL = re.compile(
    r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)+$"
)


MAX_EMAIL_LENGTH = 320


def _email(value: str) -> str:
    value = value.strip()
    if len(value) > MAX_EMAIL_LENGTH or not _EMAIL.match(value):
        raise ValueError("geçerli bir e-posta adresi değil")
    return value


EmailAddress = Annotated[str, AfterValidator(_email)]


def _strip_single_line(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if any(ch in stripped for ch in "\r\n\x00"):
        raise ValueError("satır sonu veya kontrol karakteri içeremez")
    return stripped


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


class CapabilityOut(ApiModel):
    type: ProviderType
    label: str
    default_host: str | None
    default_port: int
    default_tls: TlsMode
    tls_modes: list[TlsMode]
    auth_modes: list[AuthMode]
    planned_auth_modes: list[AuthMode]
    environments: list[AccountEnvironment]
    notes: str


class SmtpAccountBase(ApiModel):
    project_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    provider_type: ProviderType
    host: str = Field(min_length=1, max_length=253)
    port: int = Field(ge=1, le=65535)
    tls_mode: TlsMode
    auth_mode: AuthMode
    username: str | None = Field(default=None, max_length=320)
    sender_address: EmailAddress
    sender_name: str | None = Field(default=None, max_length=200)
    reply_to: EmailAddress | None = None
    environment: AccountEnvironment
    enabled: bool = True
    priority: int = Field(default=100, ge=0, le=10_000)
    timeout_seconds: int = Field(default=15, ge=1, le=120)
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=100_000)

    _strip = field_validator("name", "host", "username", "sender_name")(_strip_single_line)


class SmtpAccountCreate(SmtpAccountBase):
    # Yalnız yazılır, asla okunmaz. SMTP AUTH şifresi / uygulama şifresi.
    password: SecretStr | None = Field(default=None, max_length=1024)
    make_default: bool = False


class SmtpAccountUpdate(ApiModel):
    project_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    host: str | None = Field(default=None, min_length=1, max_length=253)
    port: int | None = Field(default=None, ge=1, le=65535)
    tls_mode: TlsMode | None = None
    auth_mode: AuthMode | None = None
    username: str | None = Field(default=None, max_length=320)
    sender_address: EmailAddress | None = None
    sender_name: str | None = Field(default=None, max_length=200)
    reply_to: EmailAddress | None = None
    environment: AccountEnvironment | None = None
    enabled: bool | None = None
    priority: int | None = Field(default=None, ge=0, le=10_000)
    timeout_seconds: int | None = Field(default=None, ge=1, le=120)
    rate_limit_per_minute: int | None = Field(default=None, ge=1, le=100_000)

    _strip = field_validator("name", "host", "username", "sender_name")(_strip_single_line)


class SecretRotate(ApiModel):
    password: SecretStr = Field(min_length=1, max_length=1024)


class SmtpAccountOut(ApiModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    provider_type: ProviderType
    host: str
    port: int
    tls_mode: TlsMode
    auth_mode: AuthMode
    username: str | None
    has_secret: bool
    sender_address: str
    sender_name: str | None
    reply_to: str | None
    environment: AccountEnvironment
    enabled: bool
    is_default: bool
    priority: int
    timeout_seconds: int
    rate_limit_per_minute: int | None
    last_test_at: datetime | None
    last_test_outcome: str | None
    last_success_send_at: datetime | None
    version: int
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str


class SmtpAccountPage(ApiModel):
    items: list[SmtpAccountOut]
    next_cursor: str | None


class TestStep(ApiModel):
    step: str
    outcome: str
    duration_ms: int
    error_code: str | None


class ConnectionTestOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    test_type: str
    outcome: str
    error_code: str | None
    steps: list[TestStep]
    duration_ms: int
    created_at: datetime

    @classmethod
    def from_row(cls, row: Any) -> ConnectionTestOut:
        return cls(
            id=row.id,
            account_id=row.account_id,
            test_type=row.test_type,
            outcome=row.outcome,
            error_code=row.error_code,
            steps=[TestStep.model_validate(s) for s in row.steps],
            duration_ms=row.duration_ms,
            created_at=row.created_at,
        )
