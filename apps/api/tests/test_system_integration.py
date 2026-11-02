from __future__ import annotations

from typing import Any

import httpx
import pytest
from sqlalchemy import text

from aih_api.app import create_management_app
from aih_api.infrastructure import Infrastructure
from aih_api.settings import ApiSettings

pytestmark = pytest.mark.integration


async def test_readiness_is_up_when_postgres_valkey_and_rabbit_are_reachable(env: Any) -> None:
    mgmt = env.mgmt
    response = await mgmt.get("/actuator/health/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


async def test_liveness_is_up(env: Any) -> None:
    mgmt = env.mgmt
    assert (await mgmt.get("/actuator/health/liveness")).status_code == 200


async def test_migration_created_installation_record(env: Any) -> None:
    infra = env.infra
    async with infra.engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM platform.installation"))).scalar_one() == 1


async def test_actuator_is_not_exposed_on_application_port(env: Any) -> None:
    api = env.api
    assert (await api.get("/actuator/health")).status_code == 404


async def test_system_info_echoes_correlation_id(env: Any) -> None:
    api = env.api
    response = await api.get("/v1/system/info", headers={"X-Correlation-Id": "it-correlation-0001"})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"] == "it-correlation-0001"
    assert response.json()["product"] == "Aka Integration Hub"
    assert response.json()["environment"] == "test"


async def test_unknown_path_returns_problem_detail_with_code(env: Any) -> None:
    api = env.api
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
