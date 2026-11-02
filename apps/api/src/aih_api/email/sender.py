"""SMTP üzerinden tek bir mesajı gönderir (hesap ayarları + secret ile)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

from aih_api.providers.smtp.client import SmtpError, SmtpTarget, classify, smtp_session
from aih_api.providers.smtp.network import NetworkPolicy


@dataclass(frozen=True)
class SendResult:
    accepted: bool
    error_code: str | None
    response_class: str | None
    duration_ms: int


def build_message(
    *,
    sender_address: str,
    sender_name: str | None,
    reply_to: str | None,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None,
    message_id_domain: str,
    correlation_id: str | None,
) -> EmailMessage:
    message = EmailMessage()
    message["From"] = formataddr((sender_name, sender_address)) if sender_name else sender_address
    message["To"] = recipient
    if reply_to:
        message["Reply-To"] = reply_to
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=False, usegmt=True)
    message["Message-ID"] = make_msgid(domain=message_id_domain)
    if correlation_id:
        message["X-AIH-Correlation-Id"] = correlation_id
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(text_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    return message


async def send(target: SmtpTarget, policy: NetworkPolicy, message: EmailMessage, sender: str) -> SendResult:
    started = time.perf_counter()
    try:
        async with smtp_session(target, policy) as client:
            try:
                errors, response = await client.send_message(message, sender=sender, recipients=[str(message["To"])])
            except Exception as exc:
                raise SmtpError(classify(exc)) from exc
        if errors:
            return SendResult(False, "SMTP_RECIPIENT_REFUSED", "5xx", _ms(started))
        code = response.strip()[:3] if response else ""
        return SendResult(True, None, f"{code[:1]}xx" if code[:1].isdigit() else "2xx", _ms(started))
    except SmtpError as exc:
        response_class = f"{exc.code[5]}xx" if exc.code[5:6].isdigit() else None
        return SendResult(False, exc.code, response_class, _ms(started))


def _ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
