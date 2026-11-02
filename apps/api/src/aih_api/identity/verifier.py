"""OIDC access token doğrulaması.

Güvenlik kuralları:
* Yalnızca veritabanında kayıtlı issuer'lara güvenilir; JWKS adresi token'dan değil kayıttan gelir (SSRF yok).
* İmza (RS256/ES256), ``exp``/``nbf``/``iat``, ``iss`` ve istemci (``azp``/``aud``) doğrulanır.
* Tenant token'daki bir claim'den değil issuer → tenant eşlemesinden türetilir.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterable
from typing import Any, Protocol

import jwt
from jwt import PyJWKClient

from aih_api.identity.principal import Principal, Role
from aih_api.tenancy.models import IdentityProvider, Tenant

ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "PS256"]
LEEWAY_SECONDS = 30


class AuthenticationError(Exception):
    """Kimlik doğrulanamadı (401). Mesaj istemciye dönmez."""


class KeyResolver(Protocol):
    async def signing_key(self, provider: IdentityProvider, token: str) -> Any: ...


class JwksKeyResolver:
    """Issuer başına önbellekli JWKS istemcisi."""

    def __init__(self) -> None:
        self._clients: dict[str, PyJWKClient] = {}

    def _client(self, provider: IdentityProvider) -> PyJWKClient:
        uri = provider.jwks_uri or provider.issuer.rstrip("/") + "/protocol/openid-connect/certs"
        client = self._clients.get(uri)
        if client is None:
            client = PyJWKClient(uri, cache_keys=True, lifespan=600, timeout=5)
            self._clients[uri] = client
        return client

    async def signing_key(self, provider: IdentityProvider, token: str) -> Any:
        key = await asyncio.to_thread(self._client(provider).get_signing_key_from_jwt, token)
        return key.key


def _claim_roles(claims: dict[str, Any], client_ids: Iterable[str]) -> set[str]:
    roles: set[str] = set()
    realm = claims.get("realm_access")
    if isinstance(realm, dict) and isinstance(realm.get("roles"), list):
        roles |= {str(r) for r in realm["roles"]}
    resource = claims.get("resource_access")
    if isinstance(resource, dict):
        for client_id in client_ids:
            entry = resource.get(client_id)
            if isinstance(entry, dict) and isinstance(entry.get("roles"), list):
                roles |= {str(r) for r in entry["roles"]}
    if isinstance(claims.get("roles"), list):
        roles |= {str(r) for r in claims["roles"]}
    return roles


def map_roles(provider: IdentityProvider, idp_roles: set[str]) -> frozenset[Role]:
    roles: set[Role] = set()
    if idp_roles & set(provider.platform_admin_roles or []):
        roles.add(Role.PLATFORM_ADMIN)
    if idp_roles & set(provider.tenant_admin_roles or []):
        roles.add(Role.TENANT_ADMIN)
    if idp_roles & set(provider.viewer_roles or []):
        roles.add(Role.VIEWER)
    return frozenset(roles)


class TokenVerifier:
    def __init__(self, resolver: KeyResolver | None = None) -> None:
        self.resolver = resolver or JwksKeyResolver()

    async def verify(self, token: str, lookup: Callable[[str], Any]) -> Principal:
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
        except jwt.PyJWTError as exc:
            raise AuthenticationError("malformed token") from exc
        issuer = unverified.get("iss")
        if not isinstance(issuer, str):
            raise AuthenticationError("missing issuer")
        found: tuple[IdentityProvider, Tenant] | None = await lookup(issuer)
        if found is None:
            raise AuthenticationError("untrusted issuer")
        provider, tenant = found
        try:
            key = await self.resolver.signing_key(provider, token)
            claims: dict[str, Any] = jwt.decode(
                token,
                key=key,
                algorithms=ALLOWED_ALGORITHMS,
                issuer=provider.issuer,
                leeway=LEEWAY_SECONDS,
                options={"require": ["exp", "iat", "iss", "sub"], "verify_aud": False},
            )
        except (jwt.PyJWTError, OSError) as exc:
            raise AuthenticationError("invalid token") from exc
        client = claims.get("azp")
        audience = claims.get("aud")
        audiences = {audience} if isinstance(audience, str) else set(audience or [])
        allowed = set(provider.allowed_client_ids)
        if client not in allowed and not (audiences & allowed):
            raise AuthenticationError("client not allowed")
        # Rolü eşlenmeyen kullanıcı kimliği doğrulanmış sayılır ama hiçbir izni olmaz (403, deny-by-default).
        roles = map_roles(provider, _claim_roles(claims, provider.allowed_client_ids))
        return Principal(
            subject=str(claims["sub"]),
            issuer=provider.issuer,
            tenant_id=tenant.id,
            tenant_slug=tenant.slug,
            roles=roles,
            display_name=claims.get("name") or claims.get("preferred_username"),
            email=claims.get("email"),
        )
