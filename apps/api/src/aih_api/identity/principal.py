from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum


class Role(StrEnum):
    PLATFORM_ADMIN = "PlatformAdmin"
    TENANT_ADMIN = "TenantAdmin"
    VIEWER = "Viewer"


class Permission(StrEnum):
    SMTP_ACCOUNT_READ = "smtp-account:read"
    SMTP_ACCOUNT_WRITE = "smtp-account:write"
    SMTP_ACCOUNT_TEST = "smtp-account:test"
    SMTP_ACCOUNT_SEND_TEST = "smtp-account:send-test"
    EMAIL_DELIVERY_READ = "email-delivery:read"
    CACHE_ACCOUNT_READ = "cache-account:read"
    CACHE_ACCOUNT_WRITE = "cache-account:write"
    CACHE_ACCOUNT_TEST = "cache-account:test"
    SMS_ACCOUNT_READ = "sms-account:read"
    SMS_ACCOUNT_WRITE = "sms-account:write"
    SMS_ACCOUNT_TEST = "sms-account:test"
    SMS_CREDIT_MANAGE = "sms-credit:manage"
    SMS_SEND = "sms:send"
    SMS_MESSAGE_READ = "sms-message:read"


# Rol → izin eşlemesi kodda sabittir (ADR-0006). Listede olmayan her şey reddedilir.
ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.PLATFORM_ADMIN: frozenset(Permission),
    Role.TENANT_ADMIN: frozenset(Permission),
    Role.VIEWER: frozenset(
        {
            Permission.SMTP_ACCOUNT_READ,
            Permission.EMAIL_DELIVERY_READ,
            Permission.CACHE_ACCOUNT_READ,
            Permission.SMS_ACCOUNT_READ,
            Permission.SMS_MESSAGE_READ,
        }
    ),
}


@dataclass(frozen=True)
class Principal:
    subject: str
    issuer: str
    tenant_id: uuid.UUID
    tenant_slug: str
    roles: frozenset[Role]
    display_name: str | None = None
    email: str | None = None
    via: str = "api"
    permissions: frozenset[Permission] = field(init=False)

    def __post_init__(self) -> None:
        perms: set[Permission] = set()
        for role in self.roles:
            perms |= ROLE_PERMISSIONS.get(role, frozenset())
        object.__setattr__(self, "permissions", frozenset(perms))

    @property
    def is_platform_admin(self) -> bool:
        return Role.PLATFORM_ADMIN in self.roles

    def can(self, permission: Permission) -> bool:
        return permission in self.permissions
