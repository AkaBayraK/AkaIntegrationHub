from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Header, Path, Query, Request
from pydantic import Field

from aih_api.email import sender
from aih_api.email import service as email_service
from aih_api.email.models import EmailDelivery, EmailDeliveryAttempt
from aih_api.errors import ApiError
from aih_api.identity.deps import TenantScope, require
from aih_api.identity.principal import Permission
from aih_api.providers.common import ApiModel
from aih_api.providers.smtp import service as smtp_service
from aih_api.providers.smtp.routes import smtp_context
from aih_api.providers.smtp.schemas import EmailAddress

router = APIRouter(prefix="/v1", tags=["email"])
_IDEMPOTENCY = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")

DeliveryStatus = Literal["queued", "sending", "accepted_by_smtp", "failed", "retry_scheduled", "cancelled"]


class SendTestEmail(ApiModel):
    recipient: EmailAddress
    confirm: bool = Field(description="Gerçek bir e-posta gönderileceğini onaylar; true olmalı")


class AttemptOut(ApiModel):
    attempt_no: int
    outcome: str
    smtp_response_class: str | None
    error_code: str | None
    duration_ms: int
    created_at: datetime


class DeliveryOut(ApiModel):
    id: uuid.UUID
    account_id: uuid.UUID
    kind: str
    message_id: str
    correlation_id: str | None
    idempotency_key: str
    recipient: str
    subject: str
    status: DeliveryStatus
    attempt_count: int
    last_error_code: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    attempts: list[AttemptOut] | None = None


def _mask_recipient(value: str) -> str:
    local, _, domain = value.partition("@")
    return f"{local[:1]}***@{domain}"


def _delivery_out(
    delivery: EmailDelivery, scope: TenantScope, attempts: list[EmailDeliveryAttempt] | None = None
) -> DeliveryOut:
    data = {name: getattr(delivery, name) for name in DeliveryOut.model_fields if name != "attempts"}
    if not scope.principal.can(Permission.SMTP_ACCOUNT_WRITE):
        data["recipient"] = _mask_recipient(delivery.recipient)
    out = DeliveryOut.model_validate(data)
    if attempts is not None:
        out.attempts = [
            AttemptOut.model_validate({n: getattr(a, n) for n in AttemptOut.model_fields}) for a in attempts
        ]
    return out


SendScope = Annotated[TenantScope, Depends(require(Permission.SMTP_ACCOUNT_SEND_TEST))]
ReadScope = Annotated[TenantScope, Depends(require(Permission.EMAIL_DELIVERY_READ))]


@router.post(
    "/tenants/{tenantId}/smtp-accounts/{accountId}/send-test-email",
    response_model=DeliveryOut,
    response_model_by_alias=True,
)
async def send_test_email(
    request: Request,
    payload: SendTestEmail,
    scope: SendScope,
    account_id: Annotated[uuid.UUID, Path(alias="accountId")],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> DeliveryOut:
    if not payload.confirm:
        raise ApiError(422, "AIH-EMAIL-003", "Test e-postası gönderimi onaylanmalıdır", "confirm")
    if not idempotency_key or not _IDEMPOTENCY.match(idempotency_key):
        raise ApiError(400, "AIH-COMMON-400", "Geçerli bir Idempotency-Key başlığı gerekli (8-128 karakter)")
    settings = request.app.state.settings
    allowlist = [a.strip() for a in settings.smtp_test_recipient_allowlist.split(",") if a.strip()]

    async with smtp_context(request, scope) as ctx:
        delivery, account, replay = await email_service.begin_test_delivery(
            ctx, account_id, payload.recipient, idempotency_key, allowlist
        )
        if replay:
            return _delivery_out(delivery, scope)
        secret = await smtp_service.resolve_secret(ctx, account)
        target = smtp_service.target_for(account, secret)
        text_body, html_body = email_service.test_bodies(account, delivery.correlation_id)
        message = sender.build_message(
            sender_address=account.sender_address,
            sender_name=account.sender_name,
            reply_to=account.reply_to,
            recipient=delivery.recipient,
            subject=delivery.subject,
            text_body=text_body,
            html_body=html_body,
            message_id_domain=account.sender_address.rsplit("@", 1)[-1],
            correlation_id=delivery.correlation_id,
        )
        del message["Message-ID"]
        message["Message-ID"] = delivery.message_id
        envelope_sender = account.sender_address
        delivery_id = delivery.id

    result = await sender.send(target, request.app.state.smtp_policy, message, envelope_sender)

    async with smtp_context(request, scope) as ctx:
        finished = await email_service.finish_delivery(ctx, delivery_id, result)
        _, attempts = await email_service.get_delivery(ctx, delivery_id)
        return _delivery_out(finished, scope, attempts)


@router.get("/tenants/{tenantId}/email-deliveries", response_model=list[DeliveryOut], response_model_by_alias=True)
async def list_deliveries(
    request: Request,
    scope: ReadScope,
    account_id: Annotated[uuid.UUID | None, Query(alias="accountId")] = None,
    status: DeliveryStatus | None = None,
    correlation_id: Annotated[str | None, Query(alias="correlationId", max_length=64)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[DeliveryOut]:
    async with smtp_context(request, scope) as ctx:
        rows = await email_service.list_deliveries(
            ctx, account_id=account_id, status=status, correlation_id=correlation_id, limit=limit
        )
        return [_delivery_out(r, scope) for r in rows]


@router.get(
    "/tenants/{tenantId}/email-deliveries/{deliveryId}", response_model=DeliveryOut, response_model_by_alias=True
)
async def get_delivery(
    request: Request, scope: ReadScope, delivery_id: Annotated[uuid.UUID, Path(alias="deliveryId")]
) -> DeliveryOut:
    async with smtp_context(request, scope) as ctx:
        delivery, attempts = await email_service.get_delivery(ctx, delivery_id)
        return _delivery_out(delivery, scope, attempts)
