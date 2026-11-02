"""Uygulama ve yönetim portlarını tek süreçte, graceful shutdown ile çalıştırır."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence

import uvicorn
from starlette.types import ASGIApp


async def serve(apps: Sequence[tuple[ASGIApp, int]], host: str = "0.0.0.0") -> None:  # noqa: S104 - container içinde dinler
    servers = [
        uvicorn.Server(
            uvicorn.Config(app, host=host, port=port, log_config=None, access_log=False, timeout_graceful_shutdown=20)
        )
        for app, port in apps
    ]
    await asyncio.gather(*(s.serve() for s in servers))
