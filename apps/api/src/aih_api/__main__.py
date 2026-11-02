from __future__ import annotations

import asyncio

from aih_api.app import create_app, create_management_app
from aih_api.settings import get_settings
from aih_common.logging import configure_logging
from aih_common.server import serve


def main() -> None:
    settings = get_settings()
    configure_logging("aih-api", settings.log_format, settings.log_level)
    app = create_app(settings)
    management = create_management_app(app.state.infra)
    asyncio.run(serve([(app, settings.api_port), (management, settings.api_management_port)]))


if __name__ == "__main__":
    main()
