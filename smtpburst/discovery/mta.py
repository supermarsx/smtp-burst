"""MTA-STS and DANE/TLSA discovery utilities."""

from __future__ import annotations

from typing import List
from dns import resolver


def mta_sts_policy(domain: str) -> List[str]:
    """Return TXT records for ``_mta-sts.DOMAIN``."""
    try:
        answers = resolver.resolve(f"_mta-sts.{domain}", "TXT")
        return [a.to_text() for a in answers]
    except Exception as exc:  # pragma: no cover - resolver failures vary
        return [f"error: {exc}"]


def dane_tlsa(name: str, port: int = 25) -> List[str]:
    """Return TLSA records for ``_PORT._tcp.NAME``."""
    qname = f"_{port}._tcp.{name}"
    try:
        answers = resolver.resolve(qname, "TLSA")
        return [a.to_text() for a in answers]
    except Exception as exc:  # pragma: no cover - resolver failures vary
        return [f"error: {exc}"]
