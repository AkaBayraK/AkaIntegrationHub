from __future__ import annotations

import asyncio

from aih_common.logging import configure_logging
from aih_common.server import serve
from aih_worker.settings import WorkerSettings
from aih_worker.worker import Worker


async def _run(settings: WorkerSettings) -> None:
    worker = Worker(settings)
    starter = asyncio.create_task(worker.start())
    try:
        await serve([(worker.management(), settings.worker_management_port)])
    finally:
        starter.cancel()
        await worker.stop()


def main() -> None:
    settings = WorkerSettings()
    configure_logging("aih-worker", settings.log_format, settings.log_level)
    asyncio.run(_run(settings))


if __name__ == "__main__":
    main()
