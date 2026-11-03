from __future__ import annotations

import ssl

from aih_api.providers.cache.client import ServerReplyError, classify, parse_info
from aih_api.providers.smtp.network import TargetNotAllowedError

INFO = """# Server\r
redis_version:7.2.4\r
server_name:valkey\r
valkey_version:8.1.4\r
server_mode:standalone\r
config_file:/etc/valkey/valkey.conf\r
executable:/usr/local/bin/valkey-server\r
uptime_in_seconds:3600\r
# Clients\r
connected_clients:3\r
# Memory\r
used_memory_human:1.20M\r
maxmemory_human:0B\r
maxmemory_policy:noeviction\r
# Replication\r
role:master\r
# Keyspace\r
db0:keys=12,expires=2,avg_ttl=0\r
db3:keys=bozuk,expires=0\r
"""


def test_parse_info_keeps_only_allowlisted_fields() -> None:
    info = parse_info(INFO)

    assert info == {
        "serverName": "valkey",
        "version": "8.1.4",
        "mode": "standalone",
        "uptimeSeconds": 3600,
        "connectedClients": 3,
        "usedMemory": "1.20M",
        "maxMemory": "0B",
        "evictionPolicy": "noeviction",
        "role": "master",
        "keyspace": {"db0": 12, "db3": 0},
    }


def test_parse_info_recognises_redis() -> None:
    info = parse_info("redis_version:7.4.1\r\nredis_mode:standalone\r\n")

    assert info["serverName"] == "redis"
    assert info["version"] == "7.4.1"


def test_classify_maps_errors_to_codes() -> None:
    assert classify(ServerReplyError("WRONGPASS")) == "CACHE_AUTH_FAILED"
    assert classify(ServerReplyError("NOAUTH")) == "CACHE_AUTH_REQUIRED"
    assert classify(ServerReplyError("ERR")) == "CACHE_SERVER_ERROR"
    assert classify(TargetNotAllowedError("SMTP_HOST_FORBIDDEN", "x")) == "CACHE_HOST_FORBIDDEN"
    assert classify(TimeoutError()) == "CACHE_TIMEOUT"
    assert classify(ssl.SSLError()) == "CACHE_TLS_FAILED"
    assert classify(ConnectionRefusedError()) == "CACHE_CONNECT_FAILED"
    assert classify(ValueError()) == "CACHE_PROTOCOL_ERROR"
