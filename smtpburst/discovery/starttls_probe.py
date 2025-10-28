"""STARTTLS version discovery for SMTP ports."""

from __future__ import annotations

from typing import Optional
import smtplib
import ssl


VERSIONS = {
    "TLSv1": ssl.TLSVersion.TLSv1,
    "TLSv1_1": ssl.TLSVersion.TLSv1_1,
    "TLSv1_2": ssl.TLSVersion.TLSv1_2,
    "TLSv1_3": ssl.TLSVersion.TLSv1_3,
}


def discover(host: str, port: int = 25, timeout: float = 5.0) -> dict[str, bool]:
    """Return mapping of TLS versions to success when using STARTTLS."""
    results: dict[str, bool] = {}
    for name, version in VERSIONS.items():
        ctx = ssl.create_default_context()
        ctx.minimum_version = version
        ctx.maximum_version = version
        try:
            with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.ehlo()
            results[name] = True
        except Exception:
            results[name] = False
    return results


def details(
    host: str, port: int = 25, timeout: float = 5.0
) -> dict[str, dict[str, object]]:
    """Return per-version STARTTLS details similar to tlstest.

    Each entry contains: supported (bool), valid (bool|None), protocol
    (str|None), cipher (str|None) and a minimal certificate summary.
    """
    out: dict[str, dict[str, object]] = {}
    for name, version in VERSIONS.items():
        info: dict[str, object] = {
            "supported": False,
            "valid": None,
            "protocol": None,
            "cipher": None,
            "certificate": None,
        }
        ctx = ssl.create_default_context()
        ctx.minimum_version = version
        ctx.maximum_version = version
        try:
            with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.ehlo()
                sslsock = getattr(smtp, "sock", None)
                proto = sslsock.version() if hasattr(sslsock, "version") else None
                cipher = sslsock.cipher()[0] if hasattr(sslsock, "cipher") else None
                cert = (
                    sslsock.getpeercert() if hasattr(sslsock, "getpeercert") else None
                )
                summary = None
                if isinstance(cert, dict):
                    summary = {
                        "subject": cert.get("subject"),
                        "issuer": cert.get("issuer"),
                        "notAfter": cert.get("notAfter"),
                    }
                # Hostname validation post-handshake, if cert present
                valid: Optional[bool] = None
                if isinstance(cert, dict):
                    # Lightweight hostname check: prefer SAN DNS entries, fallback to CN
                    try:
                        sans = [
                            v for (k, v) in cert.get("subjectAltName", []) if k == "DNS"
                        ]
                    except Exception:
                        sans = []
                    cn = None
                    try:
                        for rdn in cert.get("subject", []):
                            for t in rdn:
                                if t[0] == "commonName":
                                    cn = t[1]
                                    break
                            if cn:
                                break
                    except Exception:
                        cn = None
                    names = sans or ([cn] if cn else [])
                    valid = host in names if names else None
                info.update(
                    supported=True,
                    valid=valid,
                    protocol=proto,
                    cipher=cipher,
                    certificate=summary,
                )
        except ssl.SSLCertVerificationError:
            info["supported"] = True
            info["valid"] = False
        except Exception:
            pass
        out[name] = info
    return out


def cipher_matrix(
    host: str,
    port: int = 25,
    *,
    ciphers: Optional[list[str]] = None,
    timeout: float = 5.0,
) -> dict[str, dict[str, bool]]:
    """Return mapping of TLS versions to cipher support under STARTTLS.

    If ``ciphers`` is None, a small default list is used.
    """
    default_ciphers = [
        "TLS_AES_128_GCM_SHA256",
        "TLS_AES_256_GCM_SHA384",
        "TLS_CHACHA20_POLY1305_SHA256",
        "ECDHE-RSA-AES128-GCM-SHA256",
    ]
    cipher_list = ciphers or default_ciphers
    matrix: dict[str, dict[str, bool]] = {}
    for name, version in VERSIONS.items():
        row: dict[str, bool] = {}
        for cipher in cipher_list:
            ctx = ssl.create_default_context()
            ctx.minimum_version = version
            ctx.maximum_version = version
            try:
                ctx.set_ciphers(cipher)
            except Exception:
                row[cipher] = False
                continue
            try:
                with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                    smtp.ehlo()
                    smtp.starttls(context=ctx)
                    smtp.ehlo()
                row[cipher] = True
            except Exception:
                row[cipher] = False
        matrix[name] = row
    return matrix
