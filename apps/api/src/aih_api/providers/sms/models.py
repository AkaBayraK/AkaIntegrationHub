from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aih_api.db import Base


class SmsAccount(Base):
    __tablename__ = "sms_accounts"
    __table_args__ = {"schema": "provider"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy.tenants.id"))
    project_id: Mapped[uuid.UUID | None]
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(32))
    sender_header: Mapped[str] = mapped_column(String(11))
    username: Mapped[str | None] = mapped_column(String(100))
    # FK veritabanında var (provider.secrets); secret tablosu ORM ile eşlenmez, yalnız SecretStore erişir.
    secret_ref: Mapped[uuid.UUID | None]
    environment: Mapped[str] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    # Bakiye yalnız atomik SQL güncellemesiyle değişir (bkz. service.reserve_credit); ORM sürüm sütununu artırmaz.
    credit_balance: Mapped[int] = mapped_column(Integer, default=0)
    low_credit_threshold: Mapped[int] = mapped_column(Integer, default=100)
    console_url: Mapped[str | None] = mapped_column(String(2048))
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_test_outcome: Mapped[str | None] = mapped_column(String(16))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012


class SmsCreditTransaction(Base):
    __tablename__ = "sms_credit_transactions"
    __table_args__ = {"schema": "provider"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider.sms_accounts.id"))
    kind: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[int] = mapped_column(Integer)
    balance_after: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str | None] = mapped_column(String(200))
    message_id: Mapped[uuid.UUID | None]
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SmsMessage(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "sms"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]
    project_id: Mapped[uuid.UUID | None]
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider.sms_accounts.id"))
    kind: Mapped[str] = mapped_column(String(16))
    purpose: Mapped[str] = mapped_column(String(16))
    type_code: Mapped[str | None] = mapped_column(String(64))
    reference_type: Mapped[str | None] = mapped_column(String(64))
    reference_id: Mapped[str | None] = mapped_column(String(64))
    consent_reference: Mapped[str | None] = mapped_column(String(120))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    request_hash: Mapped[str] = mapped_column(String(64))
    phone_masked: Mapped[str] = mapped_column(String(20))
    phone_fingerprint: Mapped[str] = mapped_column(String(64))
    segments: Mapped[int] = mapped_column(Integer)
    credit_cost: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(16))
    provider_type: Mapped[str] = mapped_column(String(32))
    provider_message_id: Mapped[str | None] = mapped_column(String(100))
    error_code: Mapped[str | None] = mapped_column(String(64))
    correlation_id: Mapped[str | None] = mapped_column(String(64))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    created_by: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
