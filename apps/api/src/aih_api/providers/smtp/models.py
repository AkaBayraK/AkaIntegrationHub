from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from aih_api.db import Base


class SmtpAccount(Base):
    __tablename__ = "smtp_accounts"
    __table_args__ = {"schema": "provider"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy.tenants.id"))
    project_id: Mapped[uuid.UUID | None]
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(32))
    host: Mapped[str] = mapped_column(String(253))
    port: Mapped[int] = mapped_column(Integer)
    tls_mode: Mapped[str] = mapped_column(String(16))
    auth_mode: Mapped[str] = mapped_column(String(16))
    username: Mapped[str | None] = mapped_column(String(320))
    # FK veritabanında var (provider.secrets); secret tablosu ORM ile eşlenmez, yalnız SecretStore erişir.
    secret_ref: Mapped[uuid.UUID | None]
    sender_address: Mapped[str] = mapped_column(String(320))
    sender_name: Mapped[str | None] = mapped_column(String(200))
    reply_to: Mapped[str | None] = mapped_column(String(320))
    environment: Mapped[str] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=15)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer)
    console_url: Mapped[str | None] = mapped_column(String(2048))
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_test_outcome: Mapped[str | None] = mapped_column(String(16))
    last_success_send_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012


class SmtpConnectionTest(Base):
    __tablename__ = "smtp_connection_tests"
    __table_args__ = {"schema": "provider"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID]
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider.smtp_accounts.id"))
    test_type: Mapped[str] = mapped_column(String(32))
    outcome: Mapped[str] = mapped_column(String(16))
    error_code: Mapped[str | None] = mapped_column(String(64))
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(255))
