from __future__ import annotations

"""Network test utilities such as ping, traceroute and open relay checks."""

from dns import resolver
import ipaddress
import smtplib
import subprocess
from typing import List, Dict


def ping(host: str) -> str:
    """Return output of ``ping`` command for ``host``."""
    try:
        proc = subprocess.run(
            ["ping", "-c", "1", host],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - ping may not exist
        return str(exc)


def traceroute(host: str) -> str:
    """Return output of ``traceroute`` command for ``host``."""
    try:
        proc = subprocess.run(
            ["traceroute", host],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - traceroute may not exist
        return str(exc)


def open_relay_test(host: str, port: int = 25) -> bool:
    """Return ``True`` if ``host`` appears to be an open relay."""
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.helo("smtp-burst")
            code, _ = smtp.mail("relaytest@example.com")
            if code >= 400:
                return False
            code, _ = smtp.rcpt("recipient@example.net")
            return code < 400
    except Exception:  # pragma: no cover - network failures
        return False


def blacklist_check(ip: str, zones: List[str]) -> Dict[str, str]:
    """Return mapping of RBL zone to listing status for ``ip``."""
    results: Dict[str, str] = {}
    try:
        ip_obj = ipaddress.ip_address(ip)
    except ValueError as exc:  # pragma: no cover - input validation
        return {zone: f"error: {exc}" for zone in zones}

    if ip_obj.version == 4:
        reversed_ip = ".".join(reversed(ip.split(".")))
    else:  # pragma: no cover - IPv6 rarely used in tests
        reversed_ip = ".".join(reversed(ip_obj.exploded.split(":")))

    for zone in zones:
        qname = f"{reversed_ip}.{zone}"
        try:
            resolver.resolve(qname, "A")
            results[zone] = "listed"
        except resolver.NXDOMAIN:
            results[zone] = "not listed"
        except Exception as exc:  # pragma: no cover - resolver errors
            results[zone] = f"error: {exc}"
    return results
