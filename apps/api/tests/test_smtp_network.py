"""SSRF politikası birim testleri (ağ gerektirmez, yalnız IP literal'leri)."""

from __future__ import annotations

import pytest

from aih_api.providers.smtp.network import NetworkPolicy, TargetNotAllowed

STRICT = NetworkPolicy(allow_private=False, allowed_ports=frozenset({25, 465, 587, 2525}))
DEV = NetworkPolicy(allow_private=True, allowed_ports=frozenset({587}))


@pytest.mark.parametrize(
    "host",
    [
        "127.0.0.1",
        "10.0.0.5",
        "172.16.3.4",
        "192.168.1.10",
        "169.254.169.254",
        "0.0.0.0",
        "::1",
        "fd00::1",
        "::ffff:127.0.0.1",
        "localhost",
        "mail.internal",
        "metadata.google.internal",
        "100.64.0.1",
    ],
)
def test_strict_policy_blocks_private_and_metadata(host: str) -> None:
    with pytest.raises(TargetNotAllowed):
        STRICT.check_static(host, 587)


def test_strict_policy_blocks_unusual_ports() -> None:
    with pytest.raises(TargetNotAllowed) as exc:
        STRICT.check_static("smtp.example.com", 6379)
    assert exc.value.code == "SMTP_PORT_FORBIDDEN"


def test_public_host_allowed() -> None:
    STRICT.check_static("smtp.example.com", 587)
    STRICT.check_static("8.8.8.8", 25)


async def test_resolved_private_address_is_blocked() -> None:
    with pytest.raises(TargetNotAllowed) as exc:
        await STRICT.resolve("127.0.0.1", 587)
    assert exc.value.code == "SMTP_HOST_FORBIDDEN"


def test_allowlist() -> None:
    policy = NetworkPolicy(False, frozenset({587}), ("example.com",))
    policy.check_static("smtp.example.com", 587)
    with pytest.raises(TargetNotAllowed):
        policy.check_static("smtp.evil-example.com", 587)


def test_dev_policy_allows_local_but_still_blocks_metadata_name() -> None:
    DEV.check_static("localhost", 21025)
    with pytest.raises(TargetNotAllowed):
        DEV.check_static("metadata.google.internal", 80)
