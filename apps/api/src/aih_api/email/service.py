"""Test e-postası ve gönderim geçmişi.

Akış (çift gönderim ve kayıt kaybına karşı):
1. Transaction 1: idempotency kontrolü + ``sending`` durumunda gönderim kaydı → commit.
2. SMTP gönderimi (transaction dışında).
3. Transaction 2: deneme kaydı + ``accepted_by_smtp``/``failed`` durumu + audit.
SMTP kabulü alıcıya teslim edildiği anlamına gelmez (``accepted_by_smtp``).
"""

from __future__ import annotations

import hashlib
import html
import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError

from aih_api.audit import service as audit
from aih_api.email.models import EmailDelivery, EmailDeliveryAttempt
from aih_api.email.sender import SendResult
from aih_api.errors import ApiError
from aih_api.providers.smtp.capabilities import ProviderType
from aih_api.providers.smtp.models import SmtpAccount
from aih_api.providers.smtp.service import SmtpContext
from aih_api.providers.smtp.service import get as get_account
from aih_common import correlation

TEST_SUBJECT = "Aka Integration Hub — SMTP test e-postası"


def request_hash(payload: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def check_recipient_allowed(ctx: SmtpContext, account: SmtpAccount, recipient: str, allowlist: list[str]) -> None:
    """Test alıcısı kısıtı: kendi adresiniz, gönderen alan adı veya izinli liste. Mailpit her şeyi yakalar."""
    if account.provider_type == ProviderType.MAILPIT_TEST.value:
        return
    domain = recipient.rsplit("@", 1)[-1].lower()
    sender_domain = account.sender_address.rsplit("@", 1)[-1].lower()
    own = (ctx.principal.email or "").lower()
    allowed = {a.lower() for a in allowlist}
    if recipient.lower() == own or domain == sender_domain or recipient.lower() in allowed or domain in allowed:
        return
    raise ApiError(
        422,
        "AIH-EMAIL-002",
        "Test alıcısı kendi adresiniz, gönderen alan adı veya izinli test alıcıları olmalıdır",
        "recipient",
    )


async def begin_test_delivery(
    ctx: SmtpContext,
    account_id: uuid.UUID,
    recipient: str,
    idempotency_key: str,
    allowlist: list[str],
) -> tuple[EmailDelivery, SmtpAccount, bool]:
    """Gönderim kaydını oluşturur. Üçüncü değer: aynı anahtarla önceki kayıt döndü mü."""
    account = await get_account(ctx, account_id)
    digest = request_hash({"account": str(account_id), "recipient": recipient.lower(), "kind": "test"})
    existing = (
        await ctx.session.execute(
            select(EmailDelivery).where(
                EmailDelivery.tenant_id == ctx.tenant_id, EmailDelivery.idempotency_key == idempotency_key
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.request_hash != digest:
            raise ApiError(409, "AIH-COMMON-409", "Idempotency-Key farklı bir istekle kullanılmış")
        return existing, account, True
    if not account.enabled:
        raise ApiError(422, "AIH-EMAIL-001", "Pasif hesapla gönderim yapılamaz", "enabled")
    check_recipient_allowed(ctx, account, recipient, allowlist)
    domain = account.sender_address.rsplit("@", 1)[-1]
    delivery = EmailDelivery(
        id=uuid.uuid4(),
        tenant_id=ctx.tenant_id,
        project_id=account.project_id,
        account_id=account.id,
        kind="test",
        message_id=f"<{uuid.uuid4().hex}@{domain}>",
        correlation_id=correlation.current(),
        idempotency_key=idempotency_key,
        request_hash=digest,
        recipient=recipient,
        subject=TEST_SUBJECT,
        status="sending",
        attempt_count=0,
        created_by=ctx.principal.subject,
    )
    ctx.session.add(delivery)
    try:
        await ctx.session.flush()
    except IntegrityError as exc:  # eşzamanlı aynı anahtar
        raise ApiError(409, "AIH-COMMON-409", "Aynı Idempotency-Key ile istek işleniyor") from exc
    return delivery, account, False


def test_bodies(account: SmtpAccount, correlation_id: str | None) -> tuple[str, str]:
    now = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
    text_body = (
        "Bu, Aka Integration Hub tarafından gönderilen bir SMTP test e-postasıdır.\n\n"
        f"Hesap: {account.name}\nZaman: {now}\nKorelasyon: {correlation_id or '-'}\n\n"
        "Bu mesajı beklemiyorsanız yok sayabilirsiniz."
    )
    html_body = (
        "<p>Bu, <strong>Aka Integration Hub</strong> tarafından gönderilen bir SMTP test e-postasıdır.</p>"
        f"<ul><li>Hesap: {html.escape(account.name)}</li><li>Zaman: {now}</li>"
        f"<li>Korelasyon: {html.escape(correlation_id or '-')}</li></ul>"
    )
    return text_body, html_body


async def finish_delivery(ctx: SmtpContext, delivery_id: uuid.UUID, result: SendResult) -> EmailDelivery:
    delivery = (
        await ctx.session.execute(select(EmailDelivery).where(EmailDelivery.id == delivery_id).with_for_update())
    ).scalar_one()
    attempt_no = delivery.attempt_count + 1
    ctx.session.add(
        EmailDeliveryAttempt(
            id=uuid.uuid4(),
            tenant_id=ctx.tenant_id,
            delivery_id=delivery.id,
            account_id=delivery.account_id,
            attempt_no=attempt_no,
            outcome="accepted" if result.accepted else "failed",
            smtp_response_class=result.response_class,
            error_code=result.error_code,
            duration_ms=result.duration_ms,
        )
    )
    delivery.attempt_count = attempt_no
    delivery.status = "accepted_by_smtp" if result.accepted else "failed"
    delivery.last_error_code = result.error_code
    delivery.updated_at = datetime.now(UTC)
    if result.accepted:
        await ctx.session.execute(
            update(SmtpAccount)
            .where(SmtpAccount.id == delivery.account_id)
            .values(last_success_send_at=func.now())
            .execution_options(synchronize_session=False)
        )
    await ctx.session.flush()
    await audit.record(
        ctx.session,
        ctx.principal,
        action="smtp-account.send-test-email",
        resource_type="email-delivery",
        resource_id=delivery.id,
        tenant_id=ctx.tenant_id,
        outcome="success" if result.accepted else "failure",
        details={"accountId": str(delivery.account_id), "errorCode": result.error_code},
    )
    return delivery


async def list_deliveries(
    ctx: SmtpContext,
    *,
    account_id: uuid.UUID | None,
    status: str | None,
    correlation_id: str | None,
    limit: int,
) -> list[EmailDelivery]:
    query = select(EmailDelivery).where(EmailDelivery.tenant_id == ctx.tenant_id)
    if account_id is not None:
        query = query.where(EmailDelivery.account_id == account_id)
    if status is not None:
        query = query.where(EmailDelivery.status == status)
    if correlation_id is not None:
        query = query.where(EmailDelivery.correlation_id == correlation_id)
    rows = await ctx.session.execute(query.order_by(EmailDelivery.created_at.desc()).limit(limit))
    return list(rows.scalars())


async def get_delivery(ctx: SmtpContext, delivery_id: uuid.UUID) -> tuple[EmailDelivery, list[EmailDeliveryAttempt]]:
    delivery = (
        await ctx.session.execute(
            select(EmailDelivery).where(EmailDelivery.id == delivery_id, EmailDelivery.tenant_id == ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if delivery is None:
        raise ApiError(404, "AIH-COMMON-404", "Gönderim bulunamadı")
    attempts = await ctx.session.execute(
        select(EmailDeliveryAttempt)
        .where(EmailDeliveryAttempt.delivery_id == delivery_id)
        .order_by(EmailDeliveryAttempt.attempt_no)
    )
    return delivery, list(attempts.scalars())
