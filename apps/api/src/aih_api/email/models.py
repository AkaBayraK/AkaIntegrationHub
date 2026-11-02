from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aih_api.db import Base


class EmailDelivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = {"schema": "email"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]
    project_id: Mapped[uuid.UUID | None]
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider.smtp_accounts.id"))
    kind: Mapped[str] = mapped_column(String(16))
    message_id: Mapped[str] = mapped_column(String(255))
    correlation_id: Mapped[str | None] = mapped_column(String(64))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    recipient: Mapped[str] = mapped_column(String(320))
    subject: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(24))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    last_error_code: Mapped[str | None] = mapped_column(String(64))
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailDeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"
    __table_args__ = {"schema": "email"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]
    delivery_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("email.deliveries.id"))
    account_id: Mapped[uuid.UUID]
    attempt_no: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(16))
    smtp_response_class: Mapped[str | None] = mapped_column(String(8))
    error_code: Mapped[str | None] = mapped_column(String(64))
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
