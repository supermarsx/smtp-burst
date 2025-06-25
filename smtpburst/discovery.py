from __future__ import annotations

"""DNS and network discovery utilities."""

from dns import resolver
import subprocess
from typing import List, Any


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

