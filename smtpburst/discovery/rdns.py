"""Reverse DNS verification utilities."""

from __future__ import annotations

import socket


def verify(host: str) -> bool:
    """Return ``True`` if the PTR record for ``host`` resolves back to the same IP."""
    try:
        ip = socket.gethostbyname(host)
        ptr, _, _ = socket.gethostbyaddr(ip)
        forward_ip = socket.gethostbyname(ptr)
        return forward_ip == ip
    except Exception:  # pragma: no cover - network failures
        return False
