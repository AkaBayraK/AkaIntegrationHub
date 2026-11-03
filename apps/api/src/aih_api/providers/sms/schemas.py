from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, Field, SecretStr, field_validator

from aih_api.providers.common import ApiModel, ConsoleUrl, strip_single_line
from aih_api.providers.sms.capabilities import (
    SmsCreditType,
    SmsEnvironment,
    SmsMessageStatus,
    SmsProviderType,
    SmsPurpose,
)
from aih_api.providers.sms.text import is_valid_sender_header

MAX_CREDIT = 10_000_000
MAX_BODY_LENGTH = 1_000
_CODE = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def _sender_header(value: str) -> str:
    value = value.strip()
    if not is_valid_sender_header(value):
        raise ValueError("3-11 karakter; harf, rakam, boşluk, nokta ve tire")
    return value


def _code(value: str) -> str:
    if not _CODE.match(value):
        raise ValueError("yalnız harf, rakam ve . _ : - içerebilir")
    return value


SenderHeader = Annotated[str, AfterValidator(_sender_header)]
Code = Annotated[str, AfterValidator(_code)]


class SmsCapabilityOut(ApiModel):
    type: SmsProviderType
    label: str
    available: bool
    requires_credentials: bool
    environments: list[SmsEnvironment]
    notes: str


class SmsAccountCreate(ApiModel):
    project_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=120)
    provider_type: SmsProviderType
    sender_header: SenderHeader
    username: str | None = Field(default=None, max_length=100)
    # Yalnız yazılır, asla okunmaz.
    password: SecretStr | None = Field(default=None, max_length=1024)
    environment: SmsEnvironment
    enabled: bool = True
    make_default: bool = False
    low_credit_threshold: int = Field(default=100, ge=0, le=MAX_CREDIT)
    console_url: ConsoleUrl | None = None

    _strip = field_validator("name", "username")(strip_single_line)


class SmsAccountUpdate(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    sender_header: SenderHeader | None = None
    username: str | None = Field(default=None, max_length=100)
    password: SecretStr | None = Field(default=None, max_length=1024)
    environment: SmsEnvironment | None = None
    enabled: bool | None = None
    low_credit_threshold: int | None = Field(default=None, ge=0, le=MAX_CREDIT)
    console_url: ConsoleUrl | None = None

    _strip = field_validator("name", "username")(strip_single_line)


class SmsAccountOut(ApiModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    project_id: uuid.UUID | None
    name: str
    provider_type: SmsProviderType
    sender_header: str
    username: str | None
    has_secret: bool
    environment: SmsEnvironment
    enabled: bool
    is_default: bool
    credit_balance: int
    low_credit_threshold: int
    low_credit: bool
    console_url: str | None
    last_test_at: datetime | None
    last_test_outcome: str | None
    version: int
    created_at: datetime
    updated_at: datetime


class SmsAccountPage(ApiModel):
    items: list[SmsAccountOut]
    next_cursor: str | None


class CreditChange(ApiModel):
    kind: SmsCreditType = SmsCreditType.LOAD
    quantity: int = Field(ge=-MAX_CREDIT, le=MAX_CREDIT)
    reason: str | None = Field(default=None, max_length=200)

    _strip = field_validator("reason")(strip_single_line)


class CreditTransactionOut(ApiModel):
    id: uuid.UUID
    kind: SmsCreditType
    quantity: int
    balance_after: int
    reason: str | None
    message_id: uuid.UUID | None
    created_by: str
    created_at: datetime


class SmsReference(ApiModel):
    type: Code
    id: Code


class SmsSend(ApiModel):
    """Uygulamaların (BuildingFlow, TraceFlow) gönderim isteği. Metin uygulamada şablondan üretilir."""

    account_id: uuid.UUID | None = None
    environment: SmsEnvironment = SmsEnvironment.PRODUCTION
    phone: str = Field(min_length=10, max_length=20)
    body: str = Field(min_length=1, max_length=MAX_BODY_LENGTH)
    purpose: SmsPurpose
    type_code: Code | None = None
    reference: SmsReference | None = None
    # Pazarlama iletisinde İYS/ticari onay kaydının uygulamadaki kimliği zorunludur.
    consent_reference: str | None = Field(default=None, max_length=120)

    _strip = field_validator("consent_reference")(strip_single_line)


class SendTestSms(ApiModel):
    phone: str = Field(min_length=10, max_length=20)
    confirm: bool


class SmsMessageOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    purpose: SmsPurpose
    type_code: str | None
    reference_type: str | None
    reference_id: str | None
    phone_masked: str
    segments: int
    credit_cost: int
    status: SmsMessageStatus
    provider_type: SmsProviderType
    provider_message_id: str | None
    error_code: str | None
    correlation_id: str | None
    duration_ms: int | None
    created_by: str
    created_at: datetime


class SmsMessagePage(ApiModel):
    items: list[SmsMessageOut]
    next_cursor: str | None
