"""Veritabanı oturumu ve tenant bağlamı (RLS için ``SET LOCAL app.tenant_id``)."""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, engine: AsyncEngine) -> None:
        self.sessions = async_sessionmaker(engine, expire_on_commit=False)

    @asynccontextmanager
    async def transaction(self, tenant_id: uuid.UUID | None = None) -> AsyncIterator[AsyncSession]:
        """Tek transaction; ``tenant_id`` verilirse RLS bağlamı transaction'a özel ayarlanır."""
        async with self.sessions() as session, session.begin():
            if tenant_id is not None:
                await session.execute(
                    text("SELECT set_config('app.tenant_id', :tenant, true)"), {"tenant": str(tenant_id)}
                )
            yield session
