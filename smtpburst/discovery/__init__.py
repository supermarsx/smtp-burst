from __future__ import annotations

"""DNS and network discovery utilities."""

from dns import resolver
import ipaddress
import smtplib
import subprocess
import platform
from typing import Any, Dict, List
import ssl
import socket

from .. import send, rdns


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
        cmd = [
            "ping",
            "-c",
            "1",
            host,
        ]
        if platform.system().lower() == "windows":
            cmd = [
                "ping",
                "-n",
                "1",
                host,
            ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.stdout.strip()
    except Exception as exc:  # pragma: no cover - system might not have ping
        return str(exc)


def traceroute(host: str) -> str:
    """Return result of ``traceroute`` command for ``host``."""
    try:
        cmd = [
            "traceroute",
            host,
        ]
        if platform.system().lower() == "windows":
            cmd = [
                "tracert",
                host,
            ]
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
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


def lookup_mx(domain: str) -> List[str]:
    """Return MX records for ``domain``."""
    try:
        answers = resolver.resolve(domain, "MX")
        return [f"{r.preference} {r.exchange.to_text()}" for r in answers]
    except Exception as exc:  # pragma: no cover - dns resolver failures
        return [f"error: {exc}"]


def smtp_extensions(host: str, port: int = 25) -> List[str]:
    """Return list of supported SMTP extensions for ``host``."""
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            return list(smtp.esmtp_features.keys())
    except Exception as exc:  # pragma: no cover - network failures
        return [f"error: {exc}"]



def check_certificate(host: str, port: int = 443) -> Dict[str, Any]:
    """Return TLS certificate details for ``host``."""
    try:
        pem = ssl.get_server_certificate((host, port))
        cert = ssl._ssl._test_decode_cert(pem)
        return {
            "subject": cert.get("subject"),
            "issuer": cert.get("issuer"),
            "not_before": cert.get("notBefore"),
            "not_after": cert.get("notAfter"),
        }
    except Exception as exc:  # pragma: no cover - network/ssl failures
        return {"error": str(exc)}


def port_scan(host: str, ports: List[int], timeout: float = 1.0) -> Dict[int, bool]:
    """Return mapping of ports to open status for ``host``."""
    results: Dict[int, bool] = {}
    for p in ports:
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
