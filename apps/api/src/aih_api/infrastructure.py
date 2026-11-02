"""PostgreSQL, Valkey ve RabbitMQ bağlantıları ve readiness kontrolleri."""

from __future__ import annotations

from dataclasses import dataclass

import aio_pika
import structlog
from aio_pika.abc import AbstractRobustConnection
from redis.asyncio import Redis
from sqlalchemy import URL, make_url, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from aih_api.settings import ApiSettings

_log = structlog.get_logger("aih.infra")


def database_url(settings: ApiSettings) -> URL:
    url = make_url(settings.db_url)
    return url.set(username=url.username or settings.db_user, password=url.password or settings.db_password or None)


@dataclass
class Infrastructure:
    engine: AsyncEngine
    valkey: Redis
    rabbit: AbstractRobustConnection | None = None

    @classmethod
    def create(cls, settings: ApiSettings) -> Infrastructure:
        engine = create_async_engine(database_url(settings), pool_pre_ping=True, pool_size=10, max_overflow=5)
        valkey = Redis(
            host=settings.valkey_host,
            port=settings.valkey_port,
            password=settings.valkey_password or None,
            socket_timeout=2,
            socket_connect_timeout=2,
        )
        return cls(engine=engine, valkey=valkey)

    async def connect_rabbit(self, settings: ApiSettings) -> None:
        try:
            self.rabbit = await aio_pika.connect_robust(settings.rabbitmq.url(), timeout=5)
        except Exception as exc:
            # Readiness DOWN olur; robust bağlantı sonraki denemede yeniden kurulur.
            _log.warning("rabbitmq_connect_failed", error=type(exc).__name__)

    async def close(self) -> None:
        if self.rabbit is not None:
            await self.rabbit.close()
        await self.valkey.aclose()
        await self.engine.dispose()

    async def check_db(self) -> bool:
        async with self.engine.connect() as conn:
            value = (await conn.execute(text("SELECT 1"))).scalar_one()
            return bool(value == 1)

    async def check_valkey(self) -> bool:
        return bool(await self.valkey.ping())

    async def check_rabbit(self) -> bool:
        return self.rabbit is not None and not self.rabbit.is_closed
