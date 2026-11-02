"""Açılışta Alembic migration'larını uygular (Flyway'in Spring açılışındaki davranışı)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import URL

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _upgrade(url: URL) -> None:
    config = Config(str(ALEMBIC_INI))
    config.attributes["db_url"] = url
    command.upgrade(config, "head")


async def upgrade_to_head(url: URL) -> None:
    # env.py kendi event loop'unu açtığı için ayrı thread'de çalışır.
    await asyncio.to_thread(_upgrade, url)
