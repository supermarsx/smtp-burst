from __future__ import annotations

"""Network test utilities such as ping, traceroute and open relay checks."""

from dns import resolver
import ipaddress
import smtplib
import subprocess
import platform
from typing import Callable, Dict, List


def ping(host: str) -> str:
    """Return output of ``ping`` command for ``host``."""
    try:
        cmd = ["ping", "-c", "1", host]
        if platform.system().lower() == "windows":
            cmd = ["ping", "-n", "1", host]
        proc = subprocess.run(
            cmd,
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
        cmd = ["traceroute", host]
        if platform.system().lower() == "windows":
            cmd = ["tracert", host]
        proc = subprocess.run(
            cmd,
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


def _enum(
    host: str, port: int, items: List[str], func: Callable[[smtplib.SMTP, str], tuple]
) -> Dict[str, bool]:
    """Return mapping of ``items`` to success status using ``func``."""
    results: Dict[str, bool] = {}
    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.helo("smtp-burst")
            for item in items:
                try:
                    code, _ = func(smtp, item)
                except smtplib.SMTPException:
                    code = 500
                results[item] = code < 400
                if getattr(smtp, "rcpt", None) and func == smtp.rcpt:
                    try:
                        smtp.rset()
                    except smtplib.SMTPException:
                        pass
    except Exception:  # pragma: no cover - network failures
        return {it: False for it in items}
    return results


def vrfy_enum(host: str, items: List[str], port: int = 25) -> Dict[str, bool]:
    """Return result of VRFY enumeration for ``items``."""
    return _enum(host, port, items, lambda s, i: s.verify(i))


def expn_enum(host: str, items: List[str], port: int = 25) -> Dict[str, bool]:
    """Return result of EXPN enumeration for ``items``."""
    return _enum(host, port, items, lambda s, i: s.expn(i))


def rcpt_enum(host: str, items: List[str], port: int = 25) -> Dict[str, bool]:
    """Return result of RCPT TO enumeration for ``items``."""

    def _rcpt(smtp: smtplib.SMTP, rcpt: str):
        smtp.mail("enum@example.com")
        return smtp.rcpt(rcpt)

    return _enum(host, port, items, _rcpt)
