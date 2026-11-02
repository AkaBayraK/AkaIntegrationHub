"""ASGI correlation id middleware.

En dış katmanda çalışır: her yanıta (500 dahil) ``X-Correlation-Id`` ekler ve beklenmeyen hataları
stacktrace sızdırmadan problem details olarak döndürür.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import structlog
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from aih_common import correlation
from aih_common.problem import problem_response

_log = structlog.get_logger("aih.http")


class CorrelationIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        correlation_id = correlation.resolve(Headers(scope=scope).get(correlation.HEADER))
        token = correlation.bind(correlation_id)
        structlog.contextvars.bind_contextvars(**{correlation.LOG_KEY: correlation_id})
        started = False

        async def send_with_header(message: Message) -> None:
            nonlocal started
            if message["type"] == "http.response.start":
                started = True
                MutableHeaders(scope=message)[correlation.HEADER] = correlation_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_header)
        except Exception:
            _log.exception("unhandled_exception", path=scope.get("path"))
            if started:
                raise
            response = problem_response(500, "An unexpected error occurred", instance=_path(scope))
            await response(scope, receive, send_with_header)
        finally:
            structlog.contextvars.unbind_contextvars(correlation.LOG_KEY)
            correlation.reset(token)


def _path(scope: MutableMapping[str, Any]) -> str | None:
    path = scope.get("path")
    return path if isinstance(path, str) else None
