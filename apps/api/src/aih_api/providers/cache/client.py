"""Valkey/Redis bağlantı testi için en küçük RESP2 istemcisi.

Bağlantı, SSRF politikasıyla doğrulanmış IP'ye açılan soket üzerinden kurulur (DNS rebinding'e karşı);
bu yüzden genel amaçlı istemci kütüphanesi yerine yalnız AUTH/SELECT/PING/INFO konuşan bu modül kullanılır.
Sunucudan gelen ham hata metni dışarı verilmez; yalnız sınıflandırılmış hata kodu döner.
"""

from __future__ import annotations

import asyncio
import ssl
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from aih_api.providers.cache.capabilities import CacheAuthMode
from aih_api.providers.common import StepRecorder
from aih_api.providers.smtp.network import NetworkPolicy, TargetNotAllowedError, open_socket
from aih_api.secrets import SecretValue

MAX_BULK_BYTES = 1024 * 1024
MAX_ARRAY_ITEMS = 1024
RespValue = str | int | bytes | list["RespValue"] | None


@dataclass(frozen=True)
class CacheTarget:
    host: str
    port: int
    tls: bool
    auth_mode: CacheAuthMode
    username: str | None
    secret: SecretValue | None
    database: int
    timeout: float


class CacheError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class ServerReplyError(Exception):
    """Sunucunun '-' ile döndüğü hata; yalnız ilk kelime (hata türü) saklanır."""

    def __init__(self, kind: str) -> None:
        super().__init__(kind)
        self.kind = kind


_REPLY_CODES = {
    "WRONGPASS": "CACHE_AUTH_FAILED",
    "NOAUTH": "CACHE_AUTH_REQUIRED",
    "NOPERM": "CACHE_PERMISSION_DENIED",
}


def classify(exc: BaseException) -> str:
    if isinstance(exc, TargetNotAllowedError):
        return exc.code.replace("SMTP_", "CACHE_", 1)
    if isinstance(exc, ServerReplyError):
        return _REPLY_CODES.get(exc.kind, "CACHE_SERVER_ERROR")
    if isinstance(exc, TimeoutError):
        return "CACHE_TIMEOUT"
    if isinstance(exc, ssl.SSLError):
        return "CACHE_TLS_FAILED"
    if isinstance(exc, ConnectionError | OSError | asyncio.IncompleteReadError):
        return "CACHE_CONNECT_FAILED"
    return "CACHE_PROTOCOL_ERROR"


class RespConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, timeout: float) -> None:
        self.reader = reader
        self.writer = writer
        self.timeout = timeout

    async def command(self, *parts: str) -> RespValue:
        payload = [f"*{len(parts)}\r\n".encode()]
        for part in parts:
            data = part.encode()
            payload.append(b"$%d\r\n%s\r\n" % (len(data), data))
        self.writer.write(b"".join(payload))
        async with asyncio.timeout(self.timeout):
            await self.writer.drain()
            return await self._read()

    async def _read(self) -> RespValue:
        line = await self.reader.readuntil(b"\r\n")
        prefix, body = line[:1], line[1:-2]
        if prefix == b"+":
            return body.decode(errors="replace")
        if prefix == b"-":
            raise ServerReplyError(body.split(b" ", 1)[0].decode(errors="replace").upper())
        if prefix == b":":
            return int(body)
        if prefix == b"$":
            return await self._read_bulk(int(body))
        if prefix == b"*":
            return await self._read_array(int(body))
        raise CacheError("CACHE_PROTOCOL_ERROR")

    async def _read_bulk(self, length: int) -> bytes | None:
        if length < 0:
            return None
        if length > MAX_BULK_BYTES:
            raise CacheError("CACHE_PROTOCOL_ERROR")
        return (await self.reader.readexactly(length + 2))[:-2]

    async def _read_array(self, count: int) -> list[RespValue] | None:
        if count < 0:
            return None
        if count > MAX_ARRAY_ITEMS:
            raise CacheError("CACHE_PROTOCOL_ERROR")
        return [await self._read() for _ in range(count)]

    async def close(self) -> None:
        self.writer.close()
        try:
            await self.writer.wait_closed()
        except (OSError, ssl.SSLError):
            return


async def _authenticate(conn: RespConnection, target: CacheTarget) -> None:
    if target.auth_mode is CacheAuthMode.NONE:
        return
    if target.secret is None:
        raise CacheError("CACHE_CREDENTIALS_MISSING")
    if target.auth_mode is CacheAuthMode.ACL:
        if not target.username:
            raise CacheError("CACHE_CREDENTIALS_MISSING")
        await conn.command("AUTH", target.username, target.secret.reveal())
    else:
        await conn.command("AUTH", target.secret.reveal())


@asynccontextmanager
async def cache_session(
    target: CacheTarget, policy: NetworkPolicy, recorder: StepRecorder | None = None
) -> AsyncIterator[RespConnection]:
    """Doğrulanmış, kimliği doğrulanmış ve seçili veritabanına geçmiş bir bağlantı açar."""
    rec = recorder or StepRecorder()
    conn: RespConnection | None = None
    try:
        async with rec.step("dns"):
            addresses = await policy.resolve(target.host, target.port)
        async with rec.step("tcp"):
            sock = await open_socket(addresses, target.port, target.timeout)
        async with rec.step("tls" if target.tls else "connect"), asyncio.timeout(target.timeout):
            reader, writer = await asyncio.open_connection(
                sock=sock,
                ssl=ssl.create_default_context() if target.tls else None,
                server_hostname=target.host if target.tls else None,
            )
        conn = RespConnection(reader, writer, target.timeout)
        async with rec.step("auth"):
            await _authenticate(conn, target)
        async with rec.step("select"):
            await conn.command("SELECT", str(target.database))
        async with rec.step("ping"):
            await conn.command("PING")
    except CacheError:
        if conn is not None:
            await conn.close()
        raise
    except Exception as exc:
        if conn is not None:
            await conn.close()
        raise CacheError(classify(exc)) from exc
    if conn is None:
        raise CacheError("CACHE_PROTOCOL_ERROR")
    try:
        yield conn
    finally:
        await conn.close()


INFO_FIELDS: dict[str, str] = {
    "server_name": "serverName",
    "valkey_version": "version",
    "redis_mode": "mode",
    "server_mode": "mode",
    "uptime_in_seconds": "uptimeSeconds",
    "connected_clients": "connectedClients",
    "used_memory_human": "usedMemory",
    "maxmemory_human": "maxMemory",
    "maxmemory_policy": "evictionPolicy",
    "role": "role",
}
INTEGER_FIELDS = frozenset({"uptimeSeconds", "connectedClients"})


def parse_info(raw: str) -> dict[str, object]:
    """INFO çıktısından yalnız izinli, hassas olmayan alanları alır (yapılandırma/ağ ayrıntısı verilmez)."""
    result: dict[str, object] = {}
    keyspace: dict[str, int] = {}
    redis_version: str | None = None
    for line in raw.splitlines():
        key, sep, value = line.strip().partition(":")
        if not sep or key.startswith("#"):
            continue
        if key.startswith("db") and key[2:].isdigit():
            stats = dict(item.split("=", 1) for item in value.split(",") if "=" in item)
            keyspace[key] = int(stats.get("keys", "0")) if stats.get("keys", "0").isdigit() else 0
        elif key == "redis_version":
            redis_version = value
        elif name := INFO_FIELDS.get(key):
            result[name] = int(value) if name in INTEGER_FIELDS and value.isdigit() else value
    result.setdefault("serverName", "redis" if redis_version else None)
    if redis_version:
        result.setdefault("version", redis_version)
    result["keyspace"] = keyspace
    return result


async def server_info(conn: RespConnection) -> dict[str, object]:
    raw = await conn.command("INFO")
    if not isinstance(raw, bytes):
        raise CacheError("CACHE_PROTOCOL_ERROR")
    return parse_info(raw.decode(errors="replace"))
