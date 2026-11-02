from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
from sqlalchemy import text

from aih_api.app import create_app, create_management_app
from aih_api.infrastructure import Infrastructure
from aih_api.settings import ApiSettings
from aih_common.settings import RabbitSettings

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def settings(postgres: Any, valkey: Any, rabbitmq: Any) -> ApiSettings:
    return ApiSettings(
        environment="test",
        db_url=f"postgresql+asyncpg://{postgres.get_container_host_ip()}:{postgres.get_exposed_port(5432)}/aih",
        db_user="aih",
        db_password="test-only",
        valkey_host=valkey.host,
        valkey_port=valkey.port,
        rabbitmq=RabbitSettings(
            host=rabbitmq.host,
            port=rabbitmq.port,
            user="aih",
            password="test-only",
            vhost="aih",
        ),
    )


@pytest.fixture(scope="session")
async def clients(settings: ApiSettings) -> AsyncIterator[tuple[httpx.AsyncClient, httpx.AsyncClient, Infrastructure]]:
    app = create_app(settings)
    infra: Infrastructure = app.state.infra
    management = create_management_app(infra)
    async with app.router.lifespan_context(app):
        api = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://api")
        mgmt = httpx.AsyncClient(transport=httpx.ASGITransport(app=management), base_url="http://mgmt")
        async with api, mgmt:
            yield api, mgmt, infra


async def test_readiness_is_up_when_postgres_valkey_and_rabbit_are_reachable(clients: Any) -> None:
    _, mgmt, _ = clients
    response = await mgmt.get("/actuator/health/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


async def test_liveness_is_up(clients: Any) -> None:
    _, mgmt, _ = clients
    assert (await mgmt.get("/actuator/health/liveness")).status_code == 200


async def test_migration_created_installation_record(clients: Any) -> None:
    _, _, infra = clients
    async with infra.engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM platform.installation"))).scalar_one() == 1


async def test_actuator_is_not_exposed_on_application_port(clients: Any) -> None:
    api, _, _ = clients
    assert (await api.get("/actuator/health")).status_code == 404


async def test_system_info_echoes_correlation_id(clients: Any) -> None:
    api, _, _ = clients
    response = await api.get("/v1/system/info", headers={"X-Correlation-Id": "it-correlation-0001"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"] == "it-correlation-0001"
    assert response.json()["product"] == "Aka Integration Hub"
    assert response.json()["environment"] == "test"


async def test_unknown_path_returns_problem_detail_with_code(clients: Any) -> None:
    api, _, _ = clients
    response = await api.get("/v1/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["code"] == "AIH-COMMON-404"
    assert body["correlationId"] == response.headers["X-Correlation-Id"]
    assert "trace" not in response.text.lower()


async def test_readiness_is_down_when_valkey_is_unreachable(settings: ApiSettings) -> None:
    broken = settings.model_copy(update={"valkey_port": 1})
    infra = Infrastructure.create(broken)
    mgmt = httpx.AsyncClient(transport=httpx.ASGITransport(app=create_management_app(infra)), base_url="http://m")
    async with mgmt:
        response = await mgmt.get("/actuator/health/readiness")
    await infra.close()
    assert response.status_code == 503
    assert response.json() == {"status": "DOWN"}
