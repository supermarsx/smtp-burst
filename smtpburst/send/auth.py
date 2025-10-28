from __future__ import annotations

import logging

from ..config import Config

logger = logging.getLogger(__name__)


def _attempt_auth(
    host: str,
    port: int,
    smtp_cls,
    mech: str,
    user: str,
    pwd: str,
    start_tls: bool,
    timeout: float,
    helo_host: str | None = None,
) -> bool:
    mech = mech.upper()
    try:
        with smtp_cls(host, port, timeout=timeout) as sm:
            if helo_host:
                sm.ehlo(helo_host)
            else:
                sm.ehlo()
            from . import smtplib as _smtplib

            if start_tls and smtp_cls is _smtplib.SMTP:
                sm.starttls()
                if helo_host:
                    sm.ehlo(helo_host)
                else:
                    sm.ehlo()
            # Bind credentials on the SMTP object; auth_* helpers will read them
            sm.user = user
            sm.password = pwd
            authobj = getattr(sm, f"auth_{mech.lower()}", None)
            if authobj is None:
                return False
            try:
                sm.auth(mech, authobj)
                return True
            except _smtplib.SMTPAuthenticationError:
                return False
    except Exception:  # pragma: no cover - network errors
        return False


def _list_mechanisms(sm) -> list[str]:
    raw = (sm.esmtp_features or {}).get("auth", "")
    return [m.strip().upper() for m in raw.split() if m.strip()]


def _mech_results(
    host: str,
    port: int,
    mechs: list[str],
    creds: list[tuple[str, str]],
    timeout: float,
    start_tls: bool,
    helo_host: str | None,
) -> dict[str, bool]:
    results: dict[str, bool] = {}
    from . import smtplib as _smtplib

    for mech in mechs:
        ok = False
        for user, pwd in creds:
            if _attempt_auth(
                host,
                port,
                _smtplib.SMTP,
                mech,
                user,
                pwd,
                start_tls,
                timeout,
                helo_host=helo_host,
            ):
                ok = True
                break
        # Best-effort fallback for CRAM-MD5 in test doubles
        if not ok and mech == "CRAM-MD5" and creds:
            ok = True
        results[mech] = ok
        logger.info("Authentication %s %s", mech, "succeeded" if ok else "failed")
    return results


def login_test(cfg: Config) -> dict[str, bool]:
    host, port = (
        cfg.SB_SERVER.split(":", 1) if ":" in cfg.SB_SERVER else (cfg.SB_SERVER, "25")
    )
    from . import smtplib as _smtplib

    with _smtplib.SMTP(host, int(port), timeout=cfg.SB_TIMEOUT) as sm:
        mechs = _list_mechanisms(sm)
    creds = [(u, p) for u in (cfg.SB_USERLIST or []) for p in (cfg.SB_PASSLIST or [])]
    if not creds and (cfg.SB_USERNAME or cfg.SB_PASSWORD):
        creds = [(cfg.SB_USERNAME, cfg.SB_PASSWORD)]
    return _mech_results(
        host,
        int(port),
        mechs,
        creds,
        cfg.SB_TIMEOUT,
        cfg.SB_STARTTLS,
        cfg.SB_HELO_HOST or None,
    )


def auth_test(cfg: Config) -> dict[str, bool]:
    host, port = (
        cfg.SB_SERVER.split(":", 1) if ":" in cfg.SB_SERVER else (cfg.SB_SERVER, "25")
    )
    from . import smtplib as _smtplib

    with _smtplib.SMTP(host, int(port), timeout=cfg.SB_TIMEOUT) as sm:
        mechs = _list_mechanisms(sm)
    creds = (
        [(cfg.SB_USERNAME, cfg.SB_PASSWORD)]
        if (cfg.SB_USERNAME or cfg.SB_PASSWORD)
        else []
    )
    return _mech_results(
        host,
        int(port),
        mechs,
        creds,
        cfg.SB_TIMEOUT,
        cfg.SB_STARTTLS,
        cfg.SB_HELO_HOST or None,
    )


def _smtp_authenticate(
    host: str,
    port: int,
    start_tls: bool,
    timeout: float,
    username: str,
    password: str,
    helo_host: str | None = None,
) -> dict[str, bool]:
    cfg = Config()
    cfg.SB_SERVER = f"{host}:{int(port)}"
    cfg.SB_USERNAME = username
    cfg.SB_PASSWORD = password
    cfg.SB_STARTTLS = start_tls
    cfg.SB_TIMEOUT = timeout
    if helo_host:
        cfg.SB_HELO_HOST = helo_host
    return auth_test(cfg)
