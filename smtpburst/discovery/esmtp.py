"""ESMTP feature and compliance checks."""

from __future__ import annotations

from typing import Dict, Any, Optional
import smtplib


FEATURE_KEYS = [
    "size",
    "8bitmime",
    "smtputf8",
    "pipelining",
    "chunking",
    "dsn",
]


def check(
    host: str,
    port: int = 25,
    *,
    timeout: float = 5.0,
    test_8bit: bool = True,
    test_chunking: bool = False,
) -> Dict[str, Any]:
    """Return declared ESMTP features and simple compliance test results.

    When ``test_8bit`` is True, attempts to send a small message containing
    8-bit characters and records success. When ``test_chunking`` is True and
    CHUNKING is advertised, a placeholder chunking test is recorded as True to
    indicate support (full BDAT is not available in smtplib).
    """

    results: Dict[str, Any] = {"features": [], "supports": {}, "tests": {}}
    try:
        with smtplib.SMTP(host, port, timeout=timeout) as smtp:
            smtp.ehlo()
            feats = smtp.esmtp_features or {}
            feats_l = {
                str(k).lower(): (str(v) if v is not None else "")
                for k, v in feats.items()
            }
            fkeys = list(feats_l.keys())
            results["features"] = fkeys
            supports = {k: (k in fkeys) for k in FEATURE_KEYS}
            results["supports"] = supports
            if test_8bit:
                body = "Subject: T\n\nüber".encode("utf-8")
                try:
                    smtp.sendmail("a@b", ["c@d"], body)
                    results["tests"]["eight_bit_send"] = True
                except smtplib.SMTPDataError:
                    results["tests"]["eight_bit_send"] = False
                except Exception:
                    results["tests"]["eight_bit_send"] = False
            if supports.get("smtputf8", False):
                try:
                    # Request SMTPUTF8 in MAIL FROM with a tiny UTF-8 body
                    utf8_body = "ü".encode("utf-8")
                    smtp.sendmail("a@b", ["c@d"], utf8_body, mail_options=["SMTPUTF8"])
                    results["tests"]["smtp_utf8_send"] = True
                except smtplib.SMTPDataError:
                    results["tests"]["smtp_utf8_send"] = False
                except Exception:
                    results["tests"]["smtp_utf8_send"] = False
            size_limit: Optional[int] = None
            if supports.get("size", False):
                val = feats_l.get("size") or ""
                try:
                    size_limit = int(val)
                except ValueError:
                    size_limit = None
            if size_limit is not None and size_limit >= 0:
                try:
                    too_big = b"X" * (size_limit + 10)
                    smtp.sendmail("a@b", ["c@d"], too_big)
                    results["tests"]["size_enforced"] = False
                except smtplib.SMTPDataError:
                    results["tests"]["size_enforced"] = True
                except Exception:
                    results["tests"]["size_enforced"] = False
            if test_chunking and supports.get("chunking", False):
                # smtplib lacks BDAT API; report support based on feature flag
                results["tests"]["chunking_declared"] = True
            return results
    except Exception as exc:  # pragma: no cover - network failures
        return {"error": str(exc)}
