from __future__ import annotations
"""Legacy SSL version discovery utilities."""

from typing import Dict
import socket
import ssl

VERSIONS = {
    "SSLv3": ssl.TLSVersion.SSLv3,
}


def discover(host: str, port: int = 443, timeout: float = 3.0) -> Dict[str, bool]:
    """Return mapping of SSL version names to connection success."""
    results: Dict[str, bool] = {}
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
