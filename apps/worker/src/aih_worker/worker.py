"""Worker süreci: RabbitMQ bağlantısı ve readiness. Tüketiciler PHASE-06'da eklenir."""

from __future__ import annotations

import asyncio

import aio_pika
import structlog
from aio_pika.abc import AbstractRobustConnection
from starlette.applications import Starlette

from aih_common.health import management_app
from aih_worker.settings import WorkerSettings

_log = structlog.get_logger("aih.worker")


class Worker:
    def __init__(self, settings: WorkerSettings) -> None:
        self.settings = settings
        self.connection: AbstractRobustConnection | None = None

    async def start(self) -> None:
        while self.connection is None:
            try:
                self.connection = await aio_pika.connect_robust(self.settings.rabbitmq.url(), timeout=5)
                _log.info("rabbitmq_connected")
            except Exception as exc:
                _log.warning("rabbitmq_connect_failed", error=type(exc).__name__)
                await asyncio.sleep(2)

    async def stop(self) -> None:
        if self.connection is not None:
            await self.connection.close()

    async def check_rabbit(self) -> bool:
        return self.connection is not None and not self.connection.is_closed

    def management(self) -> Starlette:
        return management_app({"rabbit": self.check_rabbit})
