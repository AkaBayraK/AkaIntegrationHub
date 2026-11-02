"""Yönetim komutları. Örnek:

    aih-api register-tenant --slug buildingflow --name BuildingFlow \\
        --issuer http://localhost:8080/realms/buildingflow --client-id aih-admin-web \\
        --tenant-admin-roles SUPER_ADMIN,SITE_ADMIN --viewer-roles MANAGER
"""

from __future__ import annotations

import argparse
import asyncio

from aih_api.db import Database
from aih_api.infrastructure import Infrastructure, database_url
from aih_api.migrations import upgrade_to_head
from aih_api.settings import get_settings
from aih_api.tenancy import service as tenancy


def _csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


async def register_tenant(args: argparse.Namespace) -> None:
    settings = get_settings()
    await upgrade_to_head(database_url(settings))
    infra = Infrastructure.create(settings)
    try:
        async with Database(infra.engine).transaction() as session:
            tenant = await tenancy.upsert_tenant_with_issuer(
                session,
                slug=args.slug,
                name=args.name,
                issuer=args.issuer.rstrip("/"),
                client_ids=_csv(args.client_id),
                tenant_admin_roles=_csv(args.tenant_admin_roles),
                viewer_roles=_csv(args.viewer_roles),
                platform_admin_roles=_csv(args.platform_admin_roles),
                jwks_uri=args.jwks_uri,
            )
        print(f"tenant {tenant.slug} -> {tenant.id}")
    finally:
        await infra.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aih-api")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="API'yi çalıştırır (varsayılan)")
    reg = sub.add_parser("register-tenant", help="Tenant oluşturur ve bir OIDC issuer'ı ona bağlar")
    reg.add_argument("--slug", required=True)
    reg.add_argument("--name", required=True)
    reg.add_argument("--issuer", required=True, help="Ör. http://localhost:8080/realms/buildingflow")
    reg.add_argument("--client-id", required=True, help="Token'ın azp/aud değeri; virgülle birden çok")
    reg.add_argument("--tenant-admin-roles", default="")
    reg.add_argument("--viewer-roles", default="")
    reg.add_argument("--platform-admin-roles", default="")
    reg.add_argument("--jwks-uri", default=None, help="Varsayılan: <issuer>/protocol/openid-connect/certs")
    return parser


def run_command(argv: list[str] | None = None) -> bool:
    """Bir yönetim komutu çalıştırıldıysa True döner."""
    args = build_parser().parse_args(argv)
    if args.command == "register-tenant":
        asyncio.run(register_tenant(args))
        return True
    return False
