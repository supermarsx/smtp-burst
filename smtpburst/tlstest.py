"""TLS connection testing utilities."""

from __future__ import annotations

from typing import Any
import socket
import ssl

# TLS versions to test
VERSIONS = {
    "TLSv1": ssl.TLSVersion.TLSv1,
    "TLSv1_1": ssl.TLSVersion.TLSv1_1,
    "TLSv1_2": ssl.TLSVersion.TLSv1_2,
    "TLSv1_3": ssl.TLSVersion.TLSv1_3,
}


def test_versions(
    host: str,
    port: int = 443,
    timeout: float = 3.0,
) -> dict[str, dict[str, Any]]:
    """Attempt TLS connections for each version and return details."""
    results: dict[str, dict[str, Any]] = {}
    for name, ver in VERSIONS.items():
        info: dict[str, Any] = {
            "supported": False,
            "valid": None,
            "protocol": None,
            "certificate": None,
        }

        # First try with certificate verification enabled
        ctx = ssl.create_default_context()
        ctx.minimum_version = ver
        ctx.maximum_version = ver
        try:
            with socket.create_connection((host, port), timeout=timeout) as raw:
                with ctx.wrap_socket(raw, server_hostname=host) as sock:
                    info.update(
                        supported=True,
                        valid=True,
                        protocol=sock.version(),
                        certificate=sock.getpeercert(),
                    )
        except ssl.SSLCertVerificationError:
            info["supported"] = True
            info["valid"] = False
            # reconnect without verification to obtain the certificate and protocol
            try:
                nctx = ssl._create_unverified_context()
                nctx.minimum_version = ver
                nctx.maximum_version = ver
                with socket.create_connection((host, port), timeout=timeout) as raw:
                    with nctx.wrap_socket(raw, server_hostname=host) as sock:
                        info.update(
                            protocol=sock.version(),
                            certificate=sock.getpeercert(),
                        )
            except Exception:
                pass
        except Exception:
            pass

        results[name] = info
    return results
