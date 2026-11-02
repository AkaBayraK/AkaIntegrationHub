"""API ve yönetim (health) uygulama fabrikaları."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.applications import Starlette

from aih_api.db import Database
from aih_api.email.routes import router as email_router
from aih_api.errors import install_error_handlers
from aih_api.identity.deps import DEV_USER_HEADER
from aih_api.identity.routes import router as identity_router
from aih_api.identity.verifier import TokenVerifier
from aih_api.infrastructure import Infrastructure, database_url
from aih_api.migrations import upgrade_to_head
from aih_api.providers.smtp.network import NetworkPolicy
from aih_api.providers.smtp.routes import router as smtp_router
from aih_api.secrets import SecretCipher, SecretStore
from aih_api.settings import ApiSettings, get_settings
from aih_api.system import router as system_router
from aih_common.health import management_app
from aih_common.middleware import CorrelationIdMiddleware


def create_app(
    settings: ApiSettings | None = None,
    infra: Infrastructure | None = None,
    token_verifier: TokenVerifier | None = None,
) -> FastAPI:
    settings = settings or get_settings()
    infra = infra or Infrastructure.create(settings)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if settings.migrate_on_startup:
            await upgrade_to_head(database_url(settings))
        await infra.connect_rabbit(settings)
        try:
            yield
        finally:
            await infra.close()

    app = FastAPI(
        title="Aka Integration Hub API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.environment != "prod" else None,
        redoc_url=None,
    )
    app.state.settings = settings
    app.state.infra = infra
    app.state.db = Database(infra.engine)
    app.state.token_verifier = token_verifier or TokenVerifier()
    app.state.secret_store = SecretStore(SecretCipher(settings.secret_keys))
    app.state.smtp_policy = NetworkPolicy(
        allow_private=settings.smtp_allow_private_hosts,
        allowed_ports=frozenset(int(p) for p in settings.smtp_allowed_ports.split(",") if p.strip()),
        host_allowlist=tuple(h.strip().lower() for h in settings.smtp_host_allowlist.split(",") if h.strip()),
    )
    install_error_handlers(app)
    app.include_router(system_router)
    app.include_router(identity_router)
    app.include_router(smtp_router)
    app.include_router(email_router)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list(),
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "If-Match",
            "Idempotency-Key",
            "X-Correlation-Id",
            *([DEV_USER_HEADER] if settings.auth_dev_mode else []),
        ],
        expose_headers=["X-Correlation-Id", "ETag"],
        max_age=600,
    )
    app.add_middleware(CorrelationIdMiddleware)
    return app


def create_management_app(infra: Infrastructure) -> Starlette:
    return management_app({"db": infra.check_db, "redis": infra.check_valkey, "rabbit": infra.check_rabbit})
