"""FastAPI hata işleyicileri: tüm hatalar ``application/problem+json``."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from aih_common.problem import ApiErrorCode, problem_response


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> Response:
        detail = exc.detail if isinstance(exc.detail, str) and exc.status_code < 500 else None
        return problem_response(exc.status_code, detail, instance=request.url.path, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> Response:
        errors = [
            {"field": ".".join(str(p) for p in e.get("loc", ())[1:]) or "body", "message": str(e.get("msg"))}
            for e in exc.errors()
        ]
        return problem_response(
            422,
            "Request validation failed",
            instance=request.url.path,
            code=ApiErrorCode.VALIDATION_FAILED.code,
            extra={"errors": errors},
        )
