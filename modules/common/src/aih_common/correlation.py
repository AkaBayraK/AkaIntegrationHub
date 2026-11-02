"""Correlation id üretimi, doğrulaması ve istek bağlamı."""

from __future__ import annotations

import re
import uuid
from contextvars import ContextVar

HEADER = "X-Correlation-Id"
LOG_KEY = "correlationId"

_ALLOWED = re.compile(r"[A-Za-z0-9._-]{8,64}")
_current: ContextVar[str | None] = ContextVar("aih_correlation_id", default=None)


def new_id() -> str:
    return str(uuid.uuid4())


def sanitize(candidate: str | None) -> str | None:
    """Güvenli bir correlation id ise döndürür, değilse None.

    Header injection ve log forging'e karşı yalnızca sınırlı karakter kümesi ve uzunluk kabul edilir.
    """
    if candidate is None or _ALLOWED.fullmatch(candidate) is None:
        return None
    return candidate


def resolve(candidate: str | None) -> str:
    return sanitize(candidate) or new_id()


def current() -> str | None:
    return _current.get()


def bind(correlation_id: str) -> object:
    return _current.set(correlation_id)


def reset(token: object) -> None:
    _current.reset(token)  # type: ignore[arg-type]
