"""Sağlayıcı hesaplarının (SMTP, cache, ...) ortak API ve bağlantı yardımcıları."""

from __future__ import annotations

import base64
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import AfterValidator, BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from aih_api.errors import ApiError

MAX_CONSOLE_URL_LENGTH = 2048
_MIN_MASKED_HOST_LABELS = 2


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


def strip_single_line(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if any(ch in stripped for ch in "\r\n\x00"):
        raise ValueError("satır sonu veya kontrol karakteri içeremez")
    return stripped


def _console_url(value: str) -> str:
    """Yönetim arayüzü bağlantısı: yalnız http(s), kimlik bilgisi ve parça içermez."""
    value = value.strip()
    parts = urlsplit(value)
    if len(value) > MAX_CONSOLE_URL_LENGTH or parts.scheme not in ("http", "https") or not parts.hostname:
        raise ValueError("http(s) ile başlayan geçerli bir adres olmalı")
    if parts.username or parts.password:
        raise ValueError("adres kullanıcı adı veya şifre içeremez")
    if any(ch in value for ch in "\r\n\x00 "):
        raise ValueError("adres boşluk veya kontrol karakteri içeremez")
    return value


ConsoleUrl = Annotated[str, AfterValidator(_console_url)]


def encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(f"o:{offset}".encode()).decode().rstrip("=")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        raw = base64.urlsafe_b64decode(cursor + "=" * (-len(cursor) % 4)).decode()
        kind, _, value = raw.partition(":")
        offset = int(value)
    except ValueError as exc:
        raise ApiError(400, "AIH-COMMON-400", "Geçersiz cursor", "cursor") from exc
    if kind != "o" or offset < 0:
        raise ApiError(400, "AIH-COMMON-400", "Geçersiz cursor", "cursor")
    return offset


def parse_if_match(if_match: str | None) -> int:
    if not if_match:
        raise ApiError(428, "AIH-COMMON-428", "If-Match başlığı gerekli")
    raw = if_match.strip().removeprefix("W/").strip('"')
    try:
        return int(raw)
    except ValueError as exc:
        raise ApiError(400, "AIH-COMMON-400", "Geçersiz If-Match değeri") from exc


def mask(value: str | None) -> str | None:
    """Viewer rolüne gösterilen host/kullanıcı adlarını kısaltır."""
    if not value:
        return value
    head, at, domain = value.partition("@")
    if at:
        return (head[:1] + "***@" + domain) if head else value
    parts = value.split(".")
    return ".".join(["***", *parts[-2:]]) if len(parts) > _MIN_MASKED_HOST_LABELS else value[:1] + "***"


@dataclass
class Step:
    name: str
    outcome: str = "skipped"
    duration_ms: int = 0
    error_code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "step": self.name,
            "outcome": self.outcome,
            "durationMs": self.duration_ms,
            "errorCode": self.error_code,
        }


@dataclass
class StepRecorder:
    steps: list[Step] = field(default_factory=list)

    @asynccontextmanager
    async def step(self, name: str) -> AsyncIterator[Step]:
        current = Step(name)
        self.steps.append(current)
        started = time.perf_counter()
        try:
            yield current
            current.outcome = "passed"
        except Exception:
            current.outcome = "failed"
            raise
        finally:
            current.duration_ms = int((time.perf_counter() - started) * 1000)
