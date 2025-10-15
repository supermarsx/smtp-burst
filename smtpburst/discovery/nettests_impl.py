from __future__ import annotations

from typing import Callable, Dict, List


def pipelining_probe_impl(
    host: str, port: int, timeout: float, *, smtplib_module, socket_module
) -> Dict[str, bool]:
    advertised = False
    try:
        with smtplib_module.SMTP(host, port, timeout=timeout) as smtp:
            smtp.ehlo()
            advertised = "pipelining" in (smtp.esmtp_features or {})
    except Exception:  # pragma: no cover
        advertised = False

    accepted = False
    try:
        with socket_module.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                _ = s.recv(1024)
            except Exception:
                pass
            s.sendall(b"EHLO pipelining.test\r\n")
            try:
                _ = s.recv(1024)
            except Exception:
                pass
            s.sendall(b"MAIL FROM:<a@b>\r\nRCPT TO:<c@d>\r\nDATA\r\n")
            data = b""
            try:
                for _ in range(3):
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    data += chunk
            except Exception:
                pass
            text = data.decode(errors="ignore")
            accepted = ("250" in text) and ("354" in text)
    except Exception:  # pragma: no cover
        accepted = False
    return {"advertised": advertised, "accepted": accepted}


def chunking_probe_impl(
    host: str, port: int, timeout: float, *, smtplib_module, socket_module
) -> Dict[str, bool]:
    advertised = False
    try:
        with smtplib_module.SMTP(host, port, timeout=timeout) as smtp:
            smtp.ehlo()
            advertised = "chunking" in (smtp.esmtp_features or {})
    except Exception:  # pragma: no cover
        advertised = False

    accepted = False
    try:
        with socket_module.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                _ = s.recv(1024)
            except Exception:
                pass
            s.sendall(b"EHLO chunking.test\r\n")
            try:
                _ = s.recv(1024)
            except Exception:
                pass
            s.sendall(b"BDAT 4 LAST\r\nTEST")
            data = b""
            try:
                data = s.recv(1024)
            except Exception:
                pass
            text = data.decode(errors="ignore")
            accepted = "250" in text
    except Exception:  # pragma: no cover
        accepted = False
    return {"advertised": advertised, "accepted": accepted}


def enum_impl(
    host: str,
    port: int,
    items: List[str],
    func: Callable,
    reset: bool,
    *,
    smtplib_module,
) -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    try:
        with smtplib_module.SMTP(host, port, timeout=10) as smtp:
            smtp.helo("smtp-burst")
            for item in items:
                try:
                    code, _ = func(smtp, item)
                except smtplib_module.SMTPException:
                    code = 500
                results[item] = code < 400
                if reset:
                    try:
                        smtp.rset()
                    except smtplib_module.SMTPException:
                        pass
    except Exception:  # pragma: no cover
        return {it: False for it in items}
    return results
