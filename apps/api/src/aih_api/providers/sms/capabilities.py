"""SMS sağlayıcıları, mesaj amaçları ve durumları (BuildingFlow ve TraceFlow modelleriyle uyumlu)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SmsProviderType(StrEnum):
    MOCK_TEST = "mock_test"
    NETGSM = "netgsm"
    ILETI_MERKEZI = "iletimerkezi"
    VERIMOR = "verimor"
    TURKCELL = "turkcell"


class SmsPurpose(StrEnum):
    """KVKK/İYS gereği doğrulama ve operasyonel mesajlar pazarlamadan ayrı tutulur."""

    OTP = "otp"
    SECURITY = "security"
    TRANSACTIONAL = "transactional"
    OPERATIONAL = "operational"
    MARKETING = "marketing"


class SmsMessageStatus(StrEnum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"


class SmsCreditType(StrEnum):
    LOAD = "load"
    CONSUME = "consume"
    REFUND = "refund"
    ADJUST = "adjust"


class SmsEnvironment(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class SmsCapability:
    type: SmsProviderType
    label: str
    available: bool
    requires_credentials: bool
    environments: tuple[SmsEnvironment, ...]
    notes: str


SMS_CAPABILITIES: dict[SmsProviderType, SmsCapability] = {
    c.type: c
    for c in (
        SmsCapability(
            SmsProviderType.MOCK_TEST,
            "Test (gerçek SMS göndermez)",
            available=True,
            requires_credentials=False,
            environments=(SmsEnvironment.TEST,),
            notes="Yalnız dev/test platform ortamında; mesaj Hub kayıtlarına düşer, operatöre gitmez.",
        ),
        SmsCapability(
            SmsProviderType.NETGSM,
            "Netgsm",
            available=True,
            requires_credentials=True,
            environments=(SmsEnvironment.TEST, SmsEnvironment.PRODUCTION),
            notes="Kullanıcı kodu ve API şifresi; gönderici başlığı Netgsm'de onaylı olmalı.",
        ),
        SmsCapability(
            SmsProviderType.ILETI_MERKEZI,
            "İleti Merkezi",
            available=False,
            requires_credentials=True,
            environments=(SmsEnvironment.TEST, SmsEnvironment.PRODUCTION),
            notes="Adaptör planlandı.",
        ),
        SmsCapability(
            SmsProviderType.VERIMOR,
            "Verimor",
            available=False,
            requires_credentials=True,
            environments=(SmsEnvironment.TEST, SmsEnvironment.PRODUCTION),
            notes="Adaptör planlandı.",
        ),
        SmsCapability(
            SmsProviderType.TURKCELL,
            "Turkcell Mesajüssü",
            available=False,
            requires_credentials=True,
            environments=(SmsEnvironment.TEST, SmsEnvironment.PRODUCTION),
            notes="Adaptör planlandı.",
        ),
    )
}
