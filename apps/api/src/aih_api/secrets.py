"""Şifreli secret store.

Secret değerleri ``provider.secrets`` tablosunda Fernet (AES-128-CBC + HMAC-SHA256) ile şifreli tutulur.
Anahtarlar ``AIH_SECRET_KEYS`` ile verilir: ``kid1:<fernet-key>,kid2:<eski-key>``; ilki birincil anahtardır,
diğerleri yalnız çözmek için (rotasyon). Düz metin hiçbir API yanıtına, loga veya audit kaydına yazılmaz.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class SecretStoreError(Exception):
    pass


@dataclass(frozen=True)
class SecretValue:
    """``repr``/``str`` değeri asla göstermez."""

    _value: str

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretValue(***)"

    __str__ = __repr__


class SecretCipher:
    def __init__(self, keys_spec: str) -> None:
        self._keys: dict[str, Fernet] = {}
        self._primary: str | None = None
        for part in (p.strip() for p in keys_spec.split(",")):
            if not part:
                continue
            kid, sep, key = part.partition(":")
            if not sep or not kid or not key:
                raise SecretStoreError("AIH_SECRET_KEYS biçimi: kid:fernet-key[,kid:fernet-key]")
            try:
                self._keys[kid] = Fernet(key.encode())
            except ValueError as exc:
                raise SecretStoreError(f"AIH_SECRET_KEYS içindeki '{kid}' anahtarı geçersiz") from exc
            self._primary = self._primary or kid

    @property
    def configured(self) -> bool:
        return self._primary is not None

    def encrypt(self, plaintext: str) -> tuple[str, bytes]:
        if self._primary is None:
            raise SecretStoreError("AIH_SECRET_KEYS tanımlı değil")
        return self._primary, self._keys[self._primary].encrypt(plaintext.encode())

    def decrypt(self, key_id: str, ciphertext: bytes) -> SecretValue:
        fernet = self._keys.get(key_id)
        if fernet is None:
            raise SecretStoreError(f"'{key_id}' anahtarı yapılandırılmamış")
        try:
            return SecretValue(fernet.decrypt(ciphertext).decode())
        except InvalidToken as exc:
            raise SecretStoreError("secret çözülemedi") from exc

    @staticmethod
    def generate_key() -> str:
        return Fernet.generate_key().decode()


class SecretStore:
    def __init__(self, cipher: SecretCipher) -> None:
        self.cipher = cipher

    async def put(self, session: AsyncSession, tenant_id: uuid.UUID, kind: str, plaintext: str) -> uuid.UUID:
        key_id, ciphertext = self.cipher.encrypt(plaintext)
        secret_id = uuid.uuid4()
        await session.execute(
            text(
                "INSERT INTO provider.secrets (id, tenant_id, kind, key_id, ciphertext)"
                " VALUES (:id, :tenant, :kind, :kid, :ct)"
            ),
            {"id": secret_id, "tenant": tenant_id, "kind": kind, "kid": key_id, "ct": ciphertext},
        )
        return secret_id

    async def rotate(self, session: AsyncSession, secret_id: uuid.UUID, plaintext: str) -> None:
        key_id, ciphertext = self.cipher.encrypt(plaintext)
        await session.execute(
            text("UPDATE provider.secrets SET key_id = :kid, ciphertext = :ct, rotated_at = now() WHERE id = :id"),
            {"id": secret_id, "kid": key_id, "ct": ciphertext},
        )

    async def get(self, session: AsyncSession, secret_id: uuid.UUID) -> SecretValue:
        # RLS: yalnız aktif tenant'ın secret'ı görünür.
        row = (
            await session.execute(
                text("SELECT key_id, ciphertext FROM provider.secrets WHERE id = :id"), {"id": secret_id}
            )
        ).one_or_none()
        if row is None:
            raise SecretStoreError("secret bulunamadı")
        return self.cipher.decrypt(row[0], bytes(row[1]))
