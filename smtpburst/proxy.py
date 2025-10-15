"""Utilities for handling SOCKS proxies."""

from __future__ import annotations

import ipaddress
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
    scheme: Optional[str] = None  # e.g., 'http', 'https', 'socks5'


def parse_proxy(proxy: str) -> ProxyInfo:
    """Return :class:`ProxyInfo` parsed from ``proxy`` string."""

    if not proxy:
        raise ValueError("Proxy must not be empty")
    try:
        parts = urlsplit(
            proxy if "://" in proxy else f"//{proxy}", allow_fragments=False
        )
    except ValueError as exc:
        raise ValueError(f"Invalid proxy '{proxy}': {exc}") from None

    host = parts.hostname
    username = parts.username
    password = parts.password

    try:
        port = parts.port if parts.port is not None else 1080
    except ValueError:
        # Likely an IPv6 literal without brackets. Re-parse manually.
        netloc = parts.netloc
        if "@" in netloc:
            netloc = netloc.rsplit("@", 1)[1]
        host_part, sep, port_part = netloc.rpartition(":")
        if sep:
            if port_part.isdigit():
                port_int = int(port_part)
                if not (0 <= port_int <= 65535):
                    raise ValueError(f"Invalid port in proxy '{proxy}'")
                try:
                    host_ip = ipaddress.IPv6Address(host_part)
                except ipaddress.AddressValueError:
                    pass
                else:
                    host = str(host_ip)
                    return ProxyInfo(host, port_int, username, password)
            else:
                raise ValueError(f"Invalid port in proxy '{proxy}'")
        host_ip = ipaddress.IPv6Address(netloc)
        host = str(host_ip)
        port = 1080
        return ProxyInfo(host, port, username, password, parts.scheme or None)

    if host is None:
        raise ValueError(f"Invalid proxy '{proxy}'")

    # Normalize IPv6 hosts
    try:
        host = str(ipaddress.ip_address(host))
    except ValueError:
        pass

    return ProxyInfo(host, port, username, password, parts.scheme or None)


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
    try:
        info = parse_proxy(proxy)
    except ValueError as exc:
        logger.warning("Invalid proxy %s: %s", proxy, exc)
        return None
    try:
        result = ping(info.host)
    except CommandNotFoundError:
        logger.warning("Ping to proxy %s failed", proxy)
        return None
    if isinstance(result, dict):
        logger.warning("Ping to proxy %s failed: %s", proxy, result.get("error"))
        return None
    if not result:
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
            scheme = (info.scheme or "").lower()
            if scheme.startswith("socks"):
                # Minimal SOCKS5 handshake; fall back to reachability
                try:
                    if info.username or info.password:
                        sock.sendall(
                            b"\x05\x01\x02"
                        )  # version 5, 1 method, username/password
                        rep = sock.recv(2)
                        if rep != b"\x05\x02":
                            logger.warning(
                                "Proxy %s does not accept username/password auth", proxy
                            )
                            return None
                    else:
                        sock.sendall(b"\x05\x01\x00")  # version 5, 1 method, no auth
                        rep = sock.recv(2)
                        if rep != b"\x05\x00":
                            logger.warning(
                                "Proxy %s did not accept no-auth method", proxy
                            )
                            return None
                except socket.timeout:
                    logger.warning("Proxy %s timed out during SOCKS handshake", proxy)
                    return None
                except Exception as exc:  # pragma: no cover - handshake details vary
                    logger.warning(
                        "Proxy %s failed during SOCKS handshake: %s", proxy, exc
                    )
                    return None
            else:
                # Legacy behavior: validate HTTP proxy with CONNECT
                headers = [f"CONNECT {host}:{port} HTTP/1.1"]
                # Basic auth header if credentials provided
                if info.username or info.password:
                    try:
                        import base64

                        token = f"{info.username or ''}:{info.password or ''}".encode()
                        b64 = base64.b64encode(token).decode()
                        headers.append(f"Proxy-Authorization: Basic {b64}")
                    except Exception:
                        pass
                headers.append("")
                headers.append("")
                request = ("\r\n".join(headers)).encode()
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
