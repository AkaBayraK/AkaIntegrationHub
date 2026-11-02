"""SMTP sağlayıcı türleri ve yetenekleri (capability discovery)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ProviderType(StrEnum):
    CUSTOM_SMTP = "custom_smtp"
    MICROSOFT_365 = "microsoft_365"
    GOOGLE_WORKSPACE = "google_workspace"
    AMAZON_SES = "amazon_ses"
    MAILPIT_TEST = "mailpit_test"


class TlsMode(StrEnum):
    STARTTLS = "starttls"
    IMPLICIT = "implicit"
    NONE = "none"


class AuthMode(StrEnum):
    SMTP_AUTH = "smtp_auth"
    OAUTH2 = "oauth2"
    NONE = "none"


class AccountEnvironment(StrEnum):
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class Capability:
    type: ProviderType
    label: str
    default_host: str | None
    default_port: int
    default_tls: TlsMode
    tls_modes: tuple[TlsMode, ...]
    auth_modes: tuple[AuthMode, ...]
    planned_auth_modes: tuple[AuthMode, ...] = ()
    environments: tuple[AccountEnvironment, ...] = (AccountEnvironment.TEST, AccountEnvironment.PRODUCTION)
    notes: str = ""


SECURE_TLS = (TlsMode.STARTTLS, TlsMode.IMPLICIT)

CAPABILITIES: dict[ProviderType, Capability] = {
    c.type: c
    for c in (
        Capability(
            ProviderType.CUSTOM_SMTP,
            "Custom SMTP",
            None,
            587,
            TlsMode.STARTTLS,
            (*SECURE_TLS, TlsMode.NONE),
            (AuthMode.SMTP_AUTH, AuthMode.NONE),
            notes="Şifresiz mod yalnız test ortamı hesaplarında kullanılabilir.",
        ),
        Capability(
            ProviderType.MICROSOFT_365,
            "Microsoft 365",
            "smtp.office365.com",
            587,
            TlsMode.STARTTLS,
            (TlsMode.STARTTLS,),
            (AuthMode.SMTP_AUTH,),
            planned_auth_modes=(AuthMode.OAUTH2,),
            notes="SMTP AUTH kiracıda etkin olmalı; OAuth2 (XOAUTH2) sonraki dilimde.",
        ),
        Capability(
            ProviderType.GOOGLE_WORKSPACE,
            "Google Workspace",
            "smtp.gmail.com",
            587,
            TlsMode.STARTTLS,
            SECURE_TLS,
            (AuthMode.SMTP_AUTH,),
            planned_auth_modes=(AuthMode.OAUTH2,),
            notes="SMTP AUTH için uygulama şifresi gerekir; OAuth2 sonraki dilimde.",
        ),
        Capability(
            ProviderType.AMAZON_SES,
            "Amazon SES SMTP",
            "email-smtp.eu-central-1.amazonaws.com",
            587,
            TlsMode.STARTTLS,
            SECURE_TLS,
            (AuthMode.SMTP_AUTH,),
            notes="SES SMTP kimlik bilgisi IAM kullanıcı anahtarından türetilir; bölgeye göre host değişir.",
        ),
        Capability(
            ProviderType.MAILPIT_TEST,
            "Mailpit (yalnız test)",
            "localhost",
            1025,
            TlsMode.NONE,
            (TlsMode.NONE, TlsMode.STARTTLS),
            (AuthMode.NONE, AuthMode.SMTP_AUTH),
            environments=(AccountEnvironment.TEST,),
            notes="Yalnız dev/test platform ortamında ve test hesaplarında kullanılabilir.",
        ),
    )
}
