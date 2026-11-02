"""Altyapı gerektirmeyen hata modeli testleri."""

from __future__ import annotations

import httpx
from fastapi import FastAPI
from pydantic import BaseModel

from aih_api.errors import install_error_handlers
from aih_common.middleware import CorrelationIdMiddleware


class Payload(BaseModel):
    name: str


def _app() -> FastAPI:
    app = FastAPI()
    install_error_handlers(app)

    @app.get("/boom")
    async def boom() -> None:
        raise RuntimeError("database password=hunter2 leaked")

    @app.post("/items")
    async def items(payload: Payload) -> Payload:
        return payload

    app.add_middleware(CorrelationIdMiddleware)
    return app


async def test_unexpected_error_is_problem_without_internal_message() -> None:
    transport = httpx.ASGITransport(app=_app(), raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as client:
        response = await client.get("/boom", headers={"X-Correlation-Id": "boom-correlation"})
    assert response.status_code == 500
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["X-Correlation-Id"] == "boom-correlation"
    assert response.json()["code"] == "AIH-COMMON-500"
    assert "hunter2" not in response.text


async def test_validation_error_lists_fields() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app()), base_url="http://t") as client:
        response = await client.post("/items", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "AIH-COMMON-422"
    assert body["errors"][0]["field"] == "name"


async def test_unsafe_correlation_header_is_replaced() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=_app()), base_url="http://t") as client:
        response = await client.post("/items", json={"name": "x"}, headers={"X-Correlation-Id": "bad id"})
    assert response.headers["X-Correlation-Id"] != "bad id"
    assert len(response.headers["X-Correlation-Id"]) == 36
