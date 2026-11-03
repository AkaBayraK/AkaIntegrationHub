from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from aih_api.db import Base


class CacheAccount(Base):
    __tablename__ = "cache_accounts"
    __table_args__ = {"schema": "provider"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy.tenants.id"))
    project_id: Mapped[uuid.UUID | None]
    name: Mapped[str] = mapped_column(String(120))
    provider_type: Mapped[str] = mapped_column(String(32))
    host: Mapped[str] = mapped_column(String(253))
    port: Mapped[int] = mapped_column(Integer)
    tls_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auth_mode: Mapped[str] = mapped_column(String(16))
    username: Mapped[str | None] = mapped_column(String(255))
    # FK veritabanında var (provider.secrets); secret tablosu ORM ile eşlenmez, yalnız SecretStore erişir.
    secret_ref: Mapped[uuid.UUID | None]
    database_index: Mapped[int] = mapped_column(Integer, default=0)
    key_prefix: Mapped[str | None] = mapped_column(String(120))
    environment: Mapped[str] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=5)
    console_url: Mapped[str | None] = mapped_column(String(2048))
    last_test_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_test_outcome: Mapped[str | None] = mapped_column(String(16))
    server_version: Mapped[str | None] = mapped_column(String(64))
    license_type: Mapped[str | None] = mapped_column(String(32))
    license_holder: Mapped[str | None] = mapped_column(String(200))
    license_reference: Mapped[str | None] = mapped_column(String(120))
    license_expires_on: Mapped[date | None] = mapped_column(Date)
    license_key_ref: Mapped[uuid.UUID | None]
    license_acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    license_acknowledged_by: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_by: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_by: Mapped[str] = mapped_column(String(255))

    __mapper_args__ = {"version_id_col": version}  # noqa: RUF012
