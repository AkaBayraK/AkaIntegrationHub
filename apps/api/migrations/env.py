"""Alembic ortamı. Bağlantı bilgisi ``AIH_DB_*`` ayarlarından gelir; sır alembic.ini'ye yazılmaz."""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from aih_api.infrastructure import database_url
from aih_api.settings import ApiSettings

VERSION_SCHEMA = "platform"


def _run(connection: Connection) -> None:
    connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {VERSION_SCHEMA}"))
    context.configure(
        connection=connection,
        version_table="alembic_version",
        version_table_schema=VERSION_SCHEMA,
        transaction_per_migration=True,
    )
    with context.begin_transaction():
        context.run_migrations()
    connection.commit()


async def _main() -> None:
    url = context.config.attributes.get("db_url") or database_url(ApiSettings())
    engine = create_async_engine(url)
    async with engine.connect() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


asyncio.run(_main())
