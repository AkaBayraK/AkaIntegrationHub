"""SMS gönderimi.

Akış (TraceFlow ``SmsServiceImpl`` ile aynı ilke, kontör Hub'da):
1. Transaction 1: idempotency kontrolü, numara/metin/amaç doğrulaması, kontörün atomik düşülmesi ve ``queued`` kayıt.
2. Sağlayıcı çağrısı — transaction dışında (uzak çağrı veritabanı bağlantısını tutmaz).
3. Transaction 2: ``sent``; kesin hatada ``failed`` + kontör iadesi; sonucu belirsizse ``unknown`` (iade yok,
   mutabakat gerekir — çift SMS ve çift iadeye karşı).
Telefonun açık hali ve mesaj metni saklanmaz; yalnız maskeli numara, tenant tuzlu özet ve parça sayısı tutulur.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from aih_api.audit import service as audit
from aih_api.errors import ApiError
from aih_api.providers.common import decode_cursor, encode_cursor
from aih_api.providers.sms import service
from aih_api.providers.sms.capabilities import SmsCreditType, SmsMessageStatus, SmsProviderType, SmsPurpose
from aih_api.providers.sms.gateways import GatewayRequest, GatewayResult
from aih_api.providers.sms.models import SmsAccount, SmsMessage
from aih_api.providers.sms.text import MAX_SEGMENTS, mask_phone, normalize_tr_mobile, phone_fingerprint, segments
from aih_common import correlation


@dataclass(frozen=True)
class SendRequest:
    phone: str
    body: str
    purpose: SmsPurpose
    kind: str = "api"
    type_code: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    consent_reference: str | None = None


@dataclass(frozen=True)
class PendingSend:
    message_id: uuid.UUID
    provider_type: SmsProviderType
    request: GatewayRequest


def _hash(account: SmsAccount, phone: str, req: SendRequest) -> str:
    payload = {"account": str(account.id), "phone": phone, "body": req.body, "purpose": req.purpose.value}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _validate(account: SmsAccount, req: SendRequest) -> tuple[str, int]:
    if not account.enabled:
        raise ApiError(422, "AIH-SMS-012", "Pasif hesapla gönderim yapılamaz", "accountId")
    phone = normalize_tr_mobile(req.phone)
    if phone is None:
        raise ApiError(422, "AIH-SMS-013", "Geçerli bir Türkiye cep telefonu numarası değil", "phone")
    if req.purpose is SmsPurpose.MARKETING and not req.consent_reference:
        raise ApiError(422, "AIH-SMS-014", "Ticari ileti için İYS/onay kaydı belirtilmelidir", "consentReference")
    parts = segments(req.body)
    if parts > MAX_SEGMENTS:
        raise ApiError(422, "AIH-SMS-015", f"Mesaj en fazla {MAX_SEGMENTS} SMS uzunluğunda olabilir", "body")
    return phone, parts


async def begin_send(
    ctx: service.SmsContext, account: SmsAccount, req: SendRequest, idempotency_key: str
) -> SmsMessage | PendingSend:
    """Kaydı oluşturup kontörü ayırır. Aynı anahtarla önceki istek varsa o kaydı döner."""
    phone, parts = _validate(account, req)
    digest = _hash(account, phone, req)
    existing = (
        await ctx.session.execute(
            select(SmsMessage).where(
                SmsMessage.tenant_id == ctx.tenant_id, SmsMessage.idempotency_key == idempotency_key
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        if existing.request_hash != digest:
            raise ApiError(409, "AIH-COMMON-409", "Idempotency-Key farklı bir istekle kullanılmış")
        return existing
    message_id = uuid.uuid4()
    if await service.change_balance(ctx, account, -parts, kind=SmsCreditType.CONSUME, message_id=message_id) is None:
        raise ApiError(422, "AIH-SMS-016", f"Yetersiz kontör: {parts} gerekli", "credit")
    ctx.session.add(
        SmsMessage(
            id=message_id,
            tenant_id=ctx.tenant_id,
            project_id=account.project_id,
            account_id=account.id,
            kind=req.kind,
            purpose=req.purpose.value,
            type_code=req.type_code,
            reference_type=req.reference_type,
            reference_id=req.reference_id,
            consent_reference=req.consent_reference,
            idempotency_key=idempotency_key,
            request_hash=digest,
            phone_masked=mask_phone(phone),
            phone_fingerprint=phone_fingerprint(phone, str(ctx.tenant_id)),
            segments=parts,
            credit_cost=parts,
            status=SmsMessageStatus.QUEUED.value,
            provider_type=account.provider_type,
            correlation_id=correlation.current(),
            created_by=ctx.principal.subject,
        )
    )
    try:
        await ctx.session.flush()
    except IntegrityError as exc:  # eşzamanlı aynı anahtar
        raise ApiError(409, "AIH-COMMON-409", "Aynı Idempotency-Key ile istek işleniyor") from exc
    secret = await ctx.secrets.get(ctx.session, account.secret_ref) if account.secret_ref else None
    request = GatewayRequest(phone, req.body, account.sender_header, account.username, secret)
    return PendingSend(message_id, SmsProviderType(account.provider_type), request)


async def finish_send(
    ctx: service.SmsContext, message_id: uuid.UUID, result: GatewayResult, duration_ms: int
) -> SmsMessage:
    message = (
        await ctx.session.execute(select(SmsMessage).where(SmsMessage.id == message_id).with_for_update())
    ).scalar_one()
    account = await service.get(ctx, message.account_id)
    if result.outcome == "failed":
        await service.change_balance(
            ctx, account, message.credit_cost, kind=SmsCreditType.REFUND, reason="gönderilemedi", message_id=message.id
        )
    status = {"sent": SmsMessageStatus.SENT, "failed": SmsMessageStatus.FAILED}.get(
        result.outcome, SmsMessageStatus.UNKNOWN
    )
    await ctx.session.execute(
        update(SmsMessage)
        .where(SmsMessage.id == message.id)
        .values(
            status=status.value,
            provider_message_id=result.provider_message_id,
            error_code=result.error_code,
            duration_ms=duration_ms,
            updated_at=datetime.now().astimezone(),
        )
        .execution_options(synchronize_session=False)
    )
    if message.kind == "test":
        await service.record_test(
            ctx, account, "passed" if status is SmsMessageStatus.SENT else "failed", result.error_code
        )
    await audit.record(
        ctx.session,
        ctx.principal,
        action=f"sms.{message.kind}-send",
        resource_type="sms-message",
        resource_id=message.id,
        tenant_id=ctx.tenant_id,
        outcome="success" if status is SmsMessageStatus.SENT else "failure",
        details={"accountId": str(account.id), "status": status.value, "errorCode": result.error_code},
    )
    return await get_message(ctx, message.id)


async def get_message(ctx: service.SmsContext, message_id: uuid.UUID) -> SmsMessage:
    message = (
        await ctx.session.execute(
            select(SmsMessage)
            .where(SmsMessage.id == message_id, SmsMessage.tenant_id == ctx.tenant_id)
            .execution_options(populate_existing=True)
        )
    ).scalar_one_or_none()
    if message is None:
        raise ApiError(404, "AIH-COMMON-404", "SMS kaydı bulunamadı")
    return message


async def list_messages(
    ctx: service.SmsContext,
    *,
    account_id: uuid.UUID | None,
    status: SmsMessageStatus | None,
    limit: int,
    cursor: str | None,
) -> tuple[list[SmsMessage], str | None]:
    offset = decode_cursor(cursor)
    query = select(SmsMessage).where(SmsMessage.tenant_id == ctx.tenant_id)
    if account_id is not None:
        query = query.where(SmsMessage.account_id == account_id)
    if status is not None:
        query = query.where(SmsMessage.status == status.value)
    query = query.order_by(SmsMessage.created_at.desc(), SmsMessage.id)
    rows = list((await ctx.session.execute(query.offset(offset).limit(limit + 1))).scalars())
    return rows[:limit], encode_cursor(offset + limit) if len(rows) > limit else None
