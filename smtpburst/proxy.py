"""Utilities for handling SOCKS proxies."""

from __future__ import annotations

import logging
import random
import socket
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlsplit

from .discovery.nettests import CommandNotFoundError, ping

logger = logging.getLogger(__name__)


@dataclass
class ProxyInfo:
    """Structured proxy details."""

    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None


def parse_proxy(proxy: str) -> ProxyInfo:
    """Return :class:`ProxyInfo` parsed from ``proxy`` string."""

    if not proxy:
        raise ValueError("Proxy must not be empty")
    try:
        parts = urlsplit(f"//{proxy}", allow_fragments=False)
    except ValueError as exc:
        raise ValueError(f"Invalid proxy '{proxy}': {exc}") from None

    host = parts.hostname
    if host is None:
        raise ValueError(f"Invalid proxy '{proxy}'")

    try:
        port = parts.port if parts.port is not None else 1080
    except ValueError as exc:
        raise ValueError(f"Invalid port in proxy '{proxy}': {exc}") from None

    return ProxyInfo(host, port, parts.username, parts.password)


def check_proxy(
    proxy: str,
    host: str = "example.com",
    port: int = 80,
    timeout: float = 5,
) -> ProxyInfo | None:
    """Return :class:`ProxyInfo` if ``proxy`` appears reachable.

    A basic validation is performed using ping, DNS resolution and a TCP
    handshake to ``proxy`` followed by an optional HTTP CONNECT request.
    Authentication information in ``proxy`` is ignored during the validation
    but is preserved in the returned :class:`ProxyInfo` object.
    """
    info = parse_proxy(proxy)
    try:
        result = ping(info.host)
    except CommandNotFoundError:
        logger.warning("Ping to proxy %s failed", proxy)
        return None
    if not result or "timed out" in result.lower():
        logger.warning("Ping to proxy %s failed", proxy)
        return None

    try:
        socket.gethostbyname(info.host)
    except Exception as exc:  # pragma: no cover - resolution failures rare
        logger.warning("DNS lookup for proxy %s failed: %s", proxy, exc)
        return None

    try:
        with socket.create_connection((info.host, info.port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            request = f"CONNECT {host}:{port} HTTP/1.1\r\n\r\n".encode()
            try:
                sock.sendall(request)
                reply = sock.recv(1024)
                if not (
                    reply.startswith(b"HTTP/1.1 200")
                    or reply.startswith(b"HTTP/1.0 200")
                ):
                    logger.warning("Proxy %s returned unexpected status", proxy)
                    return None
            except socket.timeout:
                logger.warning("Proxy %s timed out during CONNECT", proxy)
                return None
            except Exception as exc:
                logger.warning("Proxy %s failed during CONNECT: %s", proxy, exc)
                return None
    except socket.timeout:
        logger.warning("Connection to proxy %s timed out", proxy)
        return None
    except Exception as exc:  # pragma: no cover - network errors vary
        logger.warning("Connection to proxy %s failed: %s", proxy, exc)
        return None
    return info


def load_proxies(
    path: str,
    order: str = "asc",
    check: bool = False,
    timeout: float = 5,
) -> List[str]:
    """Return list of proxies from ``path`` respecting ``order``.

    ``order`` must be one of ``"asc"``, ``"desc"`` or ``"random"``. If
    ``check`` is True, invalid proxies are filtered out using
    :func:`check_proxy` with ``timeout``.
    """
    if order not in {"asc", "desc", "random"}:
        raise ValueError(f"Unsupported order: {order}")

    with open(path, "r", encoding="utf-8") as fh:
        proxies = [line.strip() for line in fh if line.strip()]

    if order == "desc":
        proxies = list(reversed(proxies))
    elif order == "random":
        random.shuffle(proxies)

    if check:
        proxies = [p for p in proxies if check_proxy(p, timeout=timeout)]

    return proxies


def select_proxy(proxies: List[str], order: str, index: int) -> str | None:
    """Return proxy for ``index`` using ``order`` strategy.

    ``order`` must be one of ``"asc"``, ``"desc"`` or ``"random"``.
    """
    if order not in {"asc", "desc", "random"}:
        raise ValueError(f"Unsupported order: {order}")
    if not proxies:
        return None
    if order == "random":
        return random.choice(proxies)
    proxy_list = proxies if order == "asc" else list(reversed(proxies))
    return proxy_list[index % len(proxy_list)]
