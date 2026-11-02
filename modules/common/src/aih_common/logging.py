"""Yapılandırılmış JSON loglama ve hassas alan maskeleme."""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

MASK = "***"
_SENSITIVE = re.compile(r"pass(word)?|secret|token|authorization|api[_-]?key|credential|cookie", re.IGNORECASE)


def _mask(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: MASK if _SENSITIVE.search(str(k)) else _mask(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_mask(v) for v in value]
    return value


def redact_sensitive(_: Any, __: str, event_dict: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
    """Anahtar adı sır/kimlik bilgisi çağrıştıran alanları maskeler (iç içe sözlükler dahil)."""
    for key in list(event_dict):
        if key == "event":
            continue
        if _SENSITIVE.search(key):
            event_dict[key] = MASK
        else:
            event_dict[key] = _mask(event_dict[key])
    return event_dict


def configure_logging(service: str, fmt: str = "json", level: str = "INFO") -> None:
    renderer: Any = structlog.processors.JSONRenderer() if fmt != "console" else structlog.dev.ConsoleRenderer()
    shared: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True, key="@timestamp"),
        structlog.processors.CallsiteParameterAdder({structlog.processors.CallsiteParameter.MODULE}),
        lambda _l, _m, ed: {**ed, "service": service},
        redact_sensitive,
        structlog.processors.format_exc_info,
    ]
    structlog.configure(
        processors=[*shared, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelNamesMapping().get(level.upper(), 20)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(structlog.stdlib.ProcessorFormatter(foreign_pre_chain=shared, processor=renderer))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    for noisy in ("uvicorn.access",):
        logging.getLogger(noisy).setLevel(logging.WARNING)
