"""Actuator uyumlu liveness/readiness yönetim uygulaması.

Detay göstermez (``show-details: never``): yalnızca ``{"status": "UP"|"DOWN"}`` döner.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping

import structlog
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

Check = Callable[[], Awaitable[bool]]
_log = structlog.get_logger("aih.health")
CHECK_TIMEOUT_SECONDS = 2.0


async def run_checks(checks: Mapping[str, Check]) -> bool:
    async def one(name: str, check: Check) -> bool:
        try:
            return await asyncio.wait_for(check(), CHECK_TIMEOUT_SECONDS)
        except Exception as exc:  # noqa: BLE001 - her türlü bağımlılık hatası DOWN demektir
            _log.warning("readiness_check_failed", check=name, error=type(exc).__name__)
            return False

    results = await asyncio.gather(*(one(n, c) for n, c in checks.items()))
    return all(results)


def management_app(readiness: Mapping[str, Check], *, accepting: Callable[[], bool] = lambda: True) -> Starlette:
    async def liveness(_: Request) -> JSONResponse:
        return JSONResponse({"status": "UP"})

    async def ready(_: Request) -> JSONResponse:
        ok = accepting() and await run_checks(readiness)
        return JSONResponse({"status": "UP" if ok else "DOWN"}, status_code=200 if ok else 503)

    async def health(request: Request) -> JSONResponse:
        return await ready(request)

    return Starlette(
        routes=[
            Route("/actuator/health", health),
            Route("/actuator/health/liveness", liveness),
            Route("/actuator/health/readiness", ready),
        ]
    )
