from __future__ import annotations

from typing import Any

import httpx
import pytest

from aih_common.settings import RabbitSettings
from aih_worker.settings import WorkerSettings
from aih_worker.worker import Worker

pytestmark = pytest.mark.integration


async def test_readiness_is_up_when_rabbit_is_reachable(rabbitmq: Any) -> None:
    worker = Worker(
        WorkerSettings(
            rabbitmq=RabbitSettings(
                host=rabbitmq.host,
                port=rabbitmq.port,
                user="aih",
                password="test-only",
                vhost="aih",
            )
        )
    )
    await worker.start()
    try:
        transport = httpx.ASGITransport(app=worker.management())
        async with httpx.AsyncClient(transport=transport, base_url="http://w") as client:
            response = await client.get("/actuator/health/readiness")
        assert response.status_code == 200
        assert response.json() == {"status": "UP"}
    finally:
        await worker.stop()


async def test_readiness_is_down_before_connecting() -> None:
    worker = Worker(WorkerSettings())
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=worker.management()), base_url="http://w") as c:
        response = await c.get("/actuator/health/readiness")
    assert response.status_code == 503
