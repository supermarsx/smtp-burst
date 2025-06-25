from __future__ import annotations

"""Utilities for handling SOCKS proxies."""

import random
import socket
from typing import List

from .discovery.nettests import ping
from .send import parse_server


def check_proxy(proxy: str, host: str = "example.com", port: int = 80) -> bool:
    """Return ``True`` if ``proxy`` appears reachable.

    A basic validation is performed using ping, DNS resolution and a TCP
    handshake to ``proxy`` followed by an optional HTTP CONNECT request.
    """
    ph, pp = parse_server(proxy)

    if not ping(ph):
        return False
    try:
        socket.gethostbyname(ph)
    except Exception:
        return False

    try:
        with socket.create_connection((ph, pp), timeout=5) as sock:
            request = f"CONNECT {host}:{port} HTTP/1.1\r\n\r\n".encode()
            try:
                sock.sendall(request)
                sock.recv(1)
            except Exception:
                return False
    except Exception:
        return False
    return True


def load_proxies(path: str, order: str = "asc", check: bool = False) -> List[str]:
    """Return list of proxies from ``path`` respecting ``order``.

    If ``check`` is True, invalid proxies are filtered out using
    :func:`check_proxy`.
    """
    with open(path, "r", encoding="utf-8") as fh:
        proxies = [line.strip() for line in fh if line.strip()]

    if order == "desc":
        proxies = list(reversed(proxies))
    elif order == "random":
        random.shuffle(proxies)

    if check:
        proxies = [p for p in proxies if check_proxy(p)]

    return proxies


def select_proxy(proxies: List[str], order: str, index: int) -> str | None:
    """Return proxy for ``index`` using ``order`` strategy."""
    if not proxies:
        return None
    if order == "random":
        return random.choice(proxies)
    proxy_list = proxies if order == "asc" else list(reversed(proxies))
    return proxy_list[index % len(proxy_list)]
