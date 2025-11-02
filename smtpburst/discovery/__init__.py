"""DNS and network discovery utilities.

This module exposes ``ping``, ``traceroute``, ``check_rbl`` and
``test_open_relay`` from :mod:`smtpburst.discovery.nettests` for convenience.
"""

from __future__ import annotations

import asyncio
import smtplib
import socket
import ssl
from typing import Any, Iterable, Sequence

from dns import resolver

# Import discovery tests individually when used to avoid unused imports

from .nettests import (
    ping,
    traceroute,
    blacklist_check as check_rbl,
    open_relay_test as test_open_relay,
)

from .. import send
from . import rdns

__all__ = [
    "check_dmarc",
    "check_spf",
    "check_dkim",
    "check_srv",
    "check_soa",
    "check_txt",
    "lookup_mx",
    "smtp_extensions",
    "check_certificate",
    "port_scan",
    "async_port_scan",
    "probe_honeypot",
    "banner_check",
    "ping",
    "traceroute",
    "check_rbl",
    "test_open_relay",
]


def _lookup(domain: str, record: str) -> list[str]:
    """Return record strings for ``domain`` and ``record`` type."""
    try:
        answers = resolver.resolve(domain, record)
        return [ans.to_text() for ans in answers]
    except Exception as exc:  # pragma: no cover - resolver may raise many errors
        return [f"error: {exc}"]


def check_dmarc(domain: str) -> list[str]:
    """Return DMARC TXT records for ``domain``."""
    return _lookup(f"_dmarc.{domain}", "TXT")


def check_spf(domain: str) -> list[str]:
    """Return SPF TXT records for ``domain``."""
    records = _lookup(domain, "TXT")
    return [r for r in records if r.lower().startswith("v=spf1")]


def check_dkim(domain: str, selector: str = "default") -> list[str]:
    """Return DKIM TXT records for ``domain`` using ``selector``."""
    return _lookup(f"{selector}._domainkey.{domain}", "TXT")


def check_srv(name: str) -> list[str]:
    """Return SRV records for ``name``."""
    return _lookup(name, "SRV")


def check_soa(domain: str) -> list[str]:
    """Return SOA record for ``domain``."""
    return _lookup(domain, "SOA")


def check_txt(domain: str) -> list[str]:
    """Return TXT records for ``domain``."""
    return _lookup(domain, "TXT")


def lookup_mx(domain: str) -> list[str]:
    """Return MX records for ``domain``."""
    try:
        answers = resolver.resolve(domain, "MX")
        return [f"{r.preference} {r.exchange.to_text()}" for r in answers]
    except Exception as exc:  # pragma: no cover - dns resolver failures
        return [f"error: {exc}"]


def smtp_extensions(host: str, port: int = 25) -> list[str]:
    """Return list of supported SMTP extensions for ``host``."""
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            return list(smtp.esmtp_features.keys())
    except Exception as exc:  # pragma: no cover - network failures
        return [f"error: {exc}"]


def check_certificate(host: str, port: int = 443) -> dict[str, Any]:
    """Return TLS certificate details for ``host``.

    A secure connection is established using :func:`ssl.create_default_context`
    and the peer certificate is retrieved with :meth:`ssl.SSLSocket.getpeercert`.
    """
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=3) as raw:
            with ctx.wrap_socket(raw, server_hostname=host) as sock:
                cert = sock.getpeercert()
        return {
            "subject": cert.get("subject"),
            "issuer": cert.get("issuer"),
            "not_before": cert.get("notBefore"),
            "not_after": cert.get("notAfter"),
        }
    except Exception as exc:  # pragma: no cover - network/ssl failures
        return {"error": str(exc)}


def _validate_ports(ports: Sequence[int]) -> None:
    """Ensure all ``ports`` fall within the valid TCP/UDP range."""

    invalid = [p for p in ports if not 0 <= p <= 65535]
    if invalid:
        numbers = ", ".join(str(p) for p in invalid)
        raise ValueError(f"Invalid port numbers: {numbers}")


def port_scan(host: str, ports: Iterable[int], timeout: float = 1.0) -> dict[int, bool]:
    """Return mapping of ports to open status for ``host``.

    Raises ``ValueError`` if any ports are outside the range ``0``-``65535``.
    ``ports`` may be any iterable of integers.
    """

    materialised_ports = list(ports)
    _validate_ports(materialised_ports)
    results: dict[int, bool] = {}
    for p in materialised_ports:
        sock = socket.socket()
        sock.settimeout(timeout)
        try:
            sock.connect((host, p))
            results[p] = True
        except Exception:
            results[p] = False
        finally:
            sock.close()
    return results


async def async_port_scan(
    host: str,
    ports: Iterable[int],
    timeout: float = 1.0,
    limit: int = 100,
) -> dict[int, bool]:
    """Return mapping of ports to open status for ``host`` asynchronously.

    Raises ``ValueError`` if any ports are outside the range ``0``-``65535``.
    ``ports`` may be any iterable of integers.
    """

    materialised_ports = list(ports)
    _validate_ports(materialised_ports)
    results: dict[int, bool] = {}
    sem = asyncio.Semaphore(limit)

    async def probe(p: int) -> None:
        async with sem:
            try:
                _, writer = await asyncio.wait_for(
                    asyncio.open_connection(host, p),
                    timeout=timeout,
                )
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
                results[p] = True
            except Exception:
                results[p] = False

    await asyncio.gather(*(probe(p) for p in materialised_ports))
    return results


def probe_honeypot(host: str, port: int = 25) -> bool:
    """Return ``True`` if banner suggests a honeypot."""
    keywords = ("cowrie", "dionaea", "honey")
    try:
        with socket.create_connection((host, port), timeout=3) as s:
            banner = s.recv(1024).decode(errors="ignore").lower()
            return any(k in banner for k in keywords)
    except Exception:  # pragma: no cover - network issues
        return False


def banner_check(server: str) -> tuple[str, bool]:
    """Return banner string and reverse DNS status for ``server``."""
    host, port = send.parse_server(server)
    try:
        with socket.create_connection((host, port), timeout=5) as s:
            banner = s.recv(1024).decode(errors="ignore").strip()
    except Exception:  # pragma: no cover - connection errors
        return "", False
    return banner, rdns.verify(host)
