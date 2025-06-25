from __future__ import annotations

"""DNS and network discovery utilities."""

from dns import resolver
import ipaddress
import smtplib
import subprocess
from typing import List, Any, Dict


def _lookup(domain: str, record: str) -> List[str]:
    """Return record strings for ``domain`` and ``record`` type."""
    try:
        answers = resolver.resolve(domain, record)
        return [ans.to_text() for ans in answers]
    except Exception as exc:  # pragma: no cover - resolver may raise many errors
        return [f"error: {exc}"]


def check_dmarc(domain: str) -> List[str]:
    """Return DMARC TXT records for ``domain``."""
    return _lookup(f"_dmarc.{domain}", "TXT")


def check_spf(domain: str) -> List[str]:
    """Return SPF TXT records for ``domain``."""
    records = _lookup(domain, "TXT")
    return [r for r in records if r.lower().startswith("v=spf1")]


def check_dkim(domain: str, selector: str = "default") -> List[str]:
    """Return DKIM TXT records for ``domain`` using ``selector``."""
    return _lookup(f"{selector}._domainkey.{domain}", "TXT")


def check_srv(name: str) -> List[str]:
    """Return SRV records for ``name``."""
    return _lookup(name, "SRV")


def check_soa(domain: str) -> List[str]:
    """Return SOA record for ``domain``."""
    return _lookup(domain, "SOA")


def check_txt(domain: str) -> List[str]:
    """Return TXT records for ``domain``."""
    return _lookup(domain, "TXT")


def ping(host: str) -> str:
    """Return result of ``ping`` command for ``host``."""
    try:
        proc = subprocess.run([
            "ping",
            "-c",
            "1",
            host,
        ], capture_output=True, text=True, check=False)
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - system might not have ping
        return str(exc)


def traceroute(host: str) -> str:
    """Return result of ``traceroute`` command for ``host``."""
    try:
        proc = subprocess.run([
            "traceroute",
            host,
        ], capture_output=True, text=True, check=False)
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover
        return str(exc)


def check_rbl(ip: str, zones: List[str]) -> Dict[str, str]:
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
        except Exception as exc:  # pragma: no cover - other resolver errors
            results[zone] = f"error: {exc}"
    return results


def test_open_relay(host: str, port: int = 25) -> bool:
    """Return ``True`` if SMTP server appears to be an open relay."""
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.helo("smtp-burst")
            code, _ = smtp.mail("relaytest@example.com")
            if code >= 400:
                return False
            code, _ = smtp.rcpt("recipient@example.net")
            return code < 400
    except Exception:  # pragma: no cover - network errors
        return False

