"""SMTP bağlantısı (bağlantı testi ve gönderim için ortak).

Hata mesajları sağlayıcıdan gelen ham metni içermez; yalnız sınıflandırılmış hata kodu döner.
"""

from __future__ import annotations

import ssl
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

import aiosmtplib

from aih_api.providers.smtp.capabilities import AuthMode, TlsMode
from aih_api.providers.smtp.network import NetworkPolicy, TargetNotAllowedError, open_socket
from aih_api.secrets import SecretValue


@dataclass(frozen=True)
class SmtpTarget:
    host: str
    port: int
    tls_mode: TlsMode
    auth_mode: AuthMode
    username: str | None
    secret: SecretValue | None
    timeout: float


@dataclass
class Step:
    name: str
    outcome: str = "skipped"
    duration_ms: int = 0
    error_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.name,
            "outcome": self.outcome,
            "durationMs": self.duration_ms,
            "errorCode": self.error_code,
        }


@dataclass
class StepRecorder:
    steps: list[Step] = field(default_factory=list)

    @asynccontextmanager
    async def step(self, name: str) -> AsyncIterator[Step]:
        current = Step(name)
        self.steps.append(current)
        started = time.perf_counter()
        try:
            yield current
            current.outcome = "passed"
        except Exception:
            current.outcome = "failed"
            raise
        finally:
            current.duration_ms = int((time.perf_counter() - started) * 1000)


class SmtpError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_SMTP_REPLY_ERROR_MIN = 400
_SMTP_REPLY_ERROR_MAX = 600

# Sıra önemlidir: alt sınıflar (ör. SMTPAuthenticationError) üst sınıflarından önce eşleşmelidir.
_ERROR_CODES: tuple[tuple[type[BaseException] | tuple[type[BaseException], ...], str], ...] = (
    (aiosmtplib.SMTPAuthenticationError, "SMTP_AUTH_FAILED"),
    ((aiosmtplib.SMTPTimeoutError, TimeoutError), "SMTP_TIMEOUT"),
    ((ssl.SSLError, aiosmtplib.SMTPConnectTimeoutError), "SMTP_TLS_FAILED"),
    ((aiosmtplib.SMTPRecipientsRefused, aiosmtplib.SMTPRecipientRefused), "SMTP_RECIPIENT_REFUSED"),
    (aiosmtplib.SMTPSenderRefused, "SMTP_SENDER_REFUSED"),
)


def classify(exc: BaseException) -> str:
    if isinstance(exc, TargetNotAllowedError):
        return exc.code
    for types, code in _ERROR_CODES:
        if isinstance(exc, types):
            return code
    if isinstance(exc, aiosmtplib.SMTPResponseException):
        is_reply_error = _SMTP_REPLY_ERROR_MIN <= exc.code < _SMTP_REPLY_ERROR_MAX
        return f"SMTP_{exc.code}" if is_reply_error else "SMTP_PROTOCOL_ERROR"
    if isinstance(exc, ConnectionError | OSError | aiosmtplib.SMTPConnectError):
        return "SMTP_CONNECT_FAILED"
    return "SMTP_PROTOCOL_ERROR"


@asynccontextmanager
async def smtp_session(
    target: SmtpTarget, policy: NetworkPolicy, recorder: StepRecorder | None = None
) -> AsyncIterator[aiosmtplib.SMTP]:
    """Doğrulanmış, kimliği doğrulanmış bir SMTP oturumu açar ve sonunda kapatır."""
    rec = recorder or StepRecorder()
    try:
        async with rec.step("dns"):
            addresses = await policy.resolve(target.host, target.port)
        async with rec.step("tcp"):
            sock = await open_socket(addresses, target.port, target.timeout)
        client = aiosmtplib.SMTP(
            hostname=target.host,
            sock=sock,
            use_tls=target.tls_mode is TlsMode.IMPLICIT,
            start_tls=False,
            validate_certs=True,
            tls_context=ssl.create_default_context(),
            timeout=target.timeout,
        )
        async with rec.step("greeting" if target.tls_mode is not TlsMode.IMPLICIT else "tls"):
            await client.connect()
            await client.ehlo()
        if target.tls_mode is TlsMode.STARTTLS:
            async with rec.step("tls"):
                if not client.supports_extension("starttls"):
                    raise SmtpError("SMTP_STARTTLS_UNSUPPORTED")
                await client.starttls(server_hostname=target.host, tls_context=ssl.create_default_context())
                await client.ehlo()
        if target.auth_mode is AuthMode.SMTP_AUTH:
            async with rec.step("auth"):
                if target.secret is None or not target.username:
                    raise SmtpError("SMTP_CREDENTIALS_MISSING")
                await client.login(target.username, target.secret.reveal())
    except SmtpError:
        raise
    except Exception as exc:
        raise SmtpError(classify(exc)) from exc
    try:
        yield client
    finally:
        try:
            await client.quit()
        except (aiosmtplib.SMTPException, OSError, TimeoutError):
            client.close()
