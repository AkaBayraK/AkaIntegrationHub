"""RFC 9457 problem details yanıtları ve AIH hata kodları."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from http import HTTPStatus
from typing import Any

from starlette.responses import JSONResponse

from aih_common import correlation

PROBLEM_JSON = "application/problem+json"


class ApiErrorCode(Enum):
    BAD_REQUEST = ("AIH-COMMON-400", 400)
    UNAUTHORIZED = ("AIH-COMMON-401", 401)
    FORBIDDEN = ("AIH-COMMON-403", 403)
    NOT_FOUND = ("AIH-COMMON-404", 404)
    METHOD_NOT_ALLOWED = ("AIH-COMMON-405", 405)
    NOT_ACCEPTABLE = ("AIH-COMMON-406", 406)
    CONFLICT = ("AIH-COMMON-409", 409)
    UNSUPPORTED_MEDIA_TYPE = ("AIH-COMMON-415", 415)
    VALIDATION_FAILED = ("AIH-COMMON-422", 422)
    TOO_MANY_REQUESTS = ("AIH-COMMON-429", 429)
    INTERNAL_ERROR = ("AIH-COMMON-500", 500)
    SERVICE_UNAVAILABLE = ("AIH-COMMON-503", 503)

    @property
    def code(self) -> str:
        return self.value[0]

    @property
    def status(self) -> int:
        return self.value[1]

    @classmethod
    def from_status(cls, status: int) -> ApiErrorCode:
        for candidate in cls:
            if candidate.status == status:
                return candidate
        return cls.BAD_REQUEST if 400 <= status < 500 else cls.INTERNAL_ERROR


def problem_response(
    status: int,
    detail: str | None = None,
    *,
    instance: str | None = None,
    code: str | None = None,
    extra: dict[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    try:
        title = HTTPStatus(status).phrase
    except ValueError:
        title = "Error"
    body: dict[str, Any] = {"type": "about:blank", "title": title, "status": status}
    if detail:
        body["detail"] = detail
    if instance:
        body["instance"] = instance
    body["code"] = code or ApiErrorCode.from_status(status).code
    body["correlationId"] = correlation.current()
    if extra:
        body.update(extra)
    return JSONResponse(body, status_code=status, media_type=PROBLEM_JSON, headers=headers)
