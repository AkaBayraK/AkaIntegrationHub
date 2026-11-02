"""SMTP hedef doğrulaması ve SSRF koruması (THREAT_MODEL T-04).

* Host yalnız DNS adı veya IP olabilir (şema, yol, kullanıcı bilgisi yok).
* Bağlantıdan hemen önce çözülen **tüm** IP'ler kontrol edilir; özel, loopback, link-local, multicast,
  ayrılmış ve bulut metadata adresleri reddedilir (geliştirme profili hariç).
* Bağlantı, doğrulanan IP'ye açılır (DNS rebinding'e karşı); TLS doğrulaması gerçek host adıyla yapılır.
"""

from __future__ import annotations

import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass

_HOSTNAME = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*\.?$")
METADATA_HOSTS = {"metadata.google.internal", "metadata", "instance-data"}


class TargetNotAllowed(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NetworkPolicy:
    allow_private: bool
    allowed_ports: frozenset[int]
    host_allowlist: tuple[str, ...] = ()

    def check_static(self, host: str, port: int) -> None:
        """Kayıt sırasında (DNS çözmeden) yapılan kontroller."""
        candidate = host.strip().rstrip(".").lower()
        if not candidate or candidate != host.strip().lower().rstrip("."):
            raise TargetNotAllowed("SMTP_HOST_INVALID", "Host boş veya geçersiz")
        try:
            ipaddress.ip_address(candidate)
            is_ip = True
        except ValueError:
            is_ip = False
            if not _HOSTNAME.match(candidate):
                raise TargetNotAllowed("SMTP_HOST_INVALID", "Host yalnız DNS adı veya IP adresi olabilir") from None
        if candidate in METADATA_HOSTS:
            raise TargetNotAllowed("SMTP_HOST_FORBIDDEN", "Bu host'a bağlantıya izin verilmez")
        if self.host_allowlist and not any(candidate == d or candidate.endswith("." + d) for d in self.host_allowlist):
            raise TargetNotAllowed("SMTP_HOST_NOT_ALLOWLISTED", "Host izin listesinde değil")
        if not self.allow_private:
            if port not in self.allowed_ports:
                raise TargetNotAllowed("SMTP_PORT_FORBIDDEN", f"İzinli portlar: {sorted(self.allowed_ports)}")
            if is_ip:
                self._check_ip(ipaddress.ip_address(candidate))
            elif candidate == "localhost" or candidate.endswith((".localhost", ".local", ".internal")):
                raise TargetNotAllowed("SMTP_HOST_FORBIDDEN", "Yerel/iç ağ host'larına izin verilmez")

    def _check_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> None:
        if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped
        if self.allow_private:
            return
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
            or not ip.is_global
        ):
            raise TargetNotAllowed("SMTP_HOST_FORBIDDEN", "Özel veya ayrılmış ağ adreslerine bağlantıya izin verilmez")

    async def resolve(self, host: str, port: int) -> list[str]:
        """Host'u çözer ve tüm adresleri doğrular. Döndürülen IP'lerden biriyle bağlanılmalıdır."""
        self.check_static(host, port)
        loop = asyncio.get_running_loop()
        try:
            infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise TargetNotAllowed("SMTP_DNS_FAILED", "Host çözümlenemedi") from exc
        addresses = list(dict.fromkeys(str(info[4][0]) for info in infos))
        if not addresses:
            raise TargetNotAllowed("SMTP_DNS_FAILED", "Host çözümlenemedi")
        for address in addresses:
            self._check_ip(ipaddress.ip_address(address.split("%", 1)[0]))
        return addresses


async def open_socket(addresses: list[str], port: int, timeout_seconds: float) -> socket.socket:
    """Doğrulanmış IP'lerden birine TCP bağlantısı açar (non-blocking soket döner)."""
    loop = asyncio.get_running_loop()
    last_error: Exception | None = None
    for address in addresses:
        family = socket.AF_INET6 if ":" in address else socket.AF_INET
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.setblocking(False)
        try:
            async with asyncio.timeout(timeout_seconds):
                await loop.sock_connect(sock, (address, port))
            return sock
        except (OSError, TimeoutError) as exc:
            sock.close()
            last_error = exc
    raise ConnectionError("TCP bağlantısı kurulamadı") from last_error
