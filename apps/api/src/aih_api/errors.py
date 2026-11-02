"""FastAPI hata işleyicileri: tüm hatalar ``application/problem+json``."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from aih_common.problem import ApiErrorCode, problem_response


class ApiError(Exception):
    """İş kuralı hatası; ``code`` makine okunur (``AIH-<ALAN>-<NNN>``), ``field`` opsiyonel."""

    def __init__(self, status: int, code: str, detail: str, field: str | None = None) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail
        self.field = field


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error(request: Request, exc: ApiError) -> Response:
        extra = {"errors": [{"field": exc.field, "message": exc.detail}]} if exc.field else None
        return problem_response(exc.status, exc.detail, instance=request.url.path, code=exc.code, extra=extra)

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
