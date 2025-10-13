"""ESMTP feature and compliance checks."""

from __future__ import annotations

from typing import Dict, Any
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
            fkeys = [k.lower() for k in feats.keys()]
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
            if test_chunking and supports.get("chunking", False):
                # smtplib lacks BDAT API; report support based on feature flag
                results["tests"]["chunking_declared"] = True
            return results
    except Exception as exc:  # pragma: no cover - network failures
        return {"error": str(exc)}
