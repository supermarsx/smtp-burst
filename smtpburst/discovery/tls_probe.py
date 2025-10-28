"""TLS version discovery utilities."""

from __future__ import annotations

import socket
import ssl


VERSIONS = {
    "TLSv1": ssl.TLSVersion.TLSv1,
    "TLSv1_1": ssl.TLSVersion.TLSv1_1,
    "TLSv1_2": ssl.TLSVersion.TLSv1_2,
    "TLSv1_3": ssl.TLSVersion.TLSv1_3,
}


def discover(host: str, port: int = 443, timeout: float = 3.0) -> dict[str, bool]:
    """Return mapping of TLS version names to connection success."""
    results: dict[str, bool] = {}
    for name, version in VERSIONS.items():
        context = ssl.create_default_context()
        context.minimum_version = version
        context.maximum_version = version
        try:
            sock = socket.socket()
            sock.settimeout(timeout)
            with context.wrap_socket(sock, server_hostname=host) as s:
                s.connect((host, port))
            results[name] = True
        except Exception:
            results[name] = False
    return results
