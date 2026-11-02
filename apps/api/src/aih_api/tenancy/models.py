from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from aih_api.db import Base


class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = {"schema": "tenancy"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdentityProvider(Base):
    __tablename__ = "identity_providers"
    __table_args__ = {"schema": "tenancy"}  # noqa: RUF012

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenancy.tenants.id"))
    issuer: Mapped[str] = mapped_column(String(512), unique=True)
    jwks_uri: Mapped[str | None] = mapped_column(String(512))
    allowed_client_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    tenant_admin_roles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    viewer_roles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    platform_admin_roles: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
