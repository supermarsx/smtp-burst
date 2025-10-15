from __future__ import annotations

import asyncio
import ipaddress
import logging
from typing import Tuple
from urllib.parse import urlsplit

from ..config import Config
from .. import datagen, attacks  # noqa: F401
from ..proxy import parse_proxy

logger = logging.getLogger(__name__)


def throttle(cfg: Config, delay: float = 0.0) -> None:
    total = cfg.SB_GLOBAL_DELAY + delay
    if total > 0:
        from . import time as _time

        _time.sleep(total)


async def async_throttle(cfg: Config, delay: float = 0.0) -> None:
    total = cfg.SB_GLOBAL_DELAY + delay
    if total > 0:
        await asyncio.sleep(total)


from .message import append_message  # noqa: E402, F401


def sizeof_fmt(num: int, suffix: str = "B") -> str:
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


async def _async_increment(counter, lock: asyncio.Lock) -> None:
    async with lock:
        counter.value += 1


def _increment(
    counter,
    lock: asyncio.Lock | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    if lock is not None:
        if loop is None:
            loop = asyncio.get_event_loop()
        fut = asyncio.run_coroutine_threadsafe(_async_increment(counter, lock), loop)
        fut.result()
    else:
        counter.value += 1


def sendmail(
    number: int,
    burst: int,
    SB_FAILCOUNT,
    SB_MESSAGE: bytes,
    cfg: Config,
    server: str | None = None,
    proxy: str | None = None,
    users=None,
    passwords=None,
    use_ssl: bool | None = None,
    start_tls: bool | None = None,
    *,
    fail_lock: asyncio.Lock | None = None,
    loop: asyncio.AbstractEventLoop | None = None,
):
    if server is None:
        server = cfg.SB_SERVER
    if use_ssl is None:
        use_ssl = cfg.SB_SSL
    if start_tls is None:
        start_tls = cfg.SB_STARTTLS

    if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
        return

    logger.info("%s/%s, Burst %s : Sending Email", number, cfg.SB_TOTAL, burst)
    host, port = parse_server(server)
    from . import smtplib as smtplib

    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    if proxy:
        try:  # pragma: no cover - depends on PySocks
            import socks
        except ImportError:
            logger.warning("PySocks is not installed, ignoring proxy")
        else:
            try:
                pinfo = parse_proxy(proxy)
                ph, pp, user, pwd = (
                    pinfo.host,
                    pinfo.port,
                    pinfo.username,
                    pinfo.password,
                )

                class ProxySMTP(smtp_cls):
                    def _get_socket(self, host, port, timeout):
                        if timeout is not None and not timeout:
                            raise ValueError(
                                "Non-blocking socket (timeout=0) is not supported"
                            )
                        sock = socks.socksocket()
                        if user or pwd:
                            sock.set_proxy(
                                socks.SOCKS5, ph, pp, username=user, password=pwd
                            )
                        else:
                            sock.set_proxy(socks.SOCKS5, ph, pp)
                        if timeout is not None:
                            sock.settimeout(timeout)
                        if self.source_address:
                            sock.bind(self.source_address)
                        sock.connect((host, port))
                        if smtp_cls is smtplib.SMTP_SSL:
                            sock = self.context.wrap_socket(
                                sock, server_hostname=self._host
                            )
                        return sock

                smtp_cls = ProxySMTP
            except Exception:
                pass
    for attempt in range(cfg.SB_RETRY_COUNT + 1):
        throttle(cfg)
        try:
            with smtp_cls(host, port, timeout=cfg.SB_TIMEOUT) as smtpObj:
                if cfg.SB_HELO_HOST:
                    smtpObj.ehlo(cfg.SB_HELO_HOST)
                else:
                    smtpObj.ehlo()
                if start_tls and not use_ssl:
                    smtpObj.starttls()
                    if cfg.SB_HELO_HOST:
                        smtpObj.ehlo(cfg.SB_HELO_HOST)
                    else:
                        smtpObj.ehlo()
                if users and passwords:
                    success = False
                    for user in users:
                        for pwd in passwords:
                            try:
                                smtpObj.login(user, pwd)
                                logger.info("Auth success: %s:%s", user, pwd)
                                success = True
                                break
                            except smtplib.SMTPException:
                                continue
                        if success:
                            break
                from . import time as _time

                start_t = _time.monotonic()
                smtpObj.sendmail(cfg.SB_SENDER, cfg.SB_RECEIVERS, SB_MESSAGE)
                latency = _time.monotonic() - start_t
                if latency > cfg.SB_TARPIT_THRESHOLD:
                    logger.warning("Possible tarpit detected: %.2fs latency", latency)
            logger.info("%s/%s, Burst %s : Email Sent", number, cfg.SB_TOTAL, burst)
            return
        except smtplib.SMTPSenderRefused:
            if attempt < cfg.SB_RETRY_COUNT:
                continue
            _increment(SB_FAILCOUNT, fail_lock, loop)
            logger.error(
                "%s/%s, Burst %s : Failure %s/%s, Sender refused",
                number,
                cfg.SB_TOTAL,
                burst,
                SB_FAILCOUNT.value,
                cfg.SB_STOPFQNT,
            )
        except smtplib.SMTPRecipientsRefused:
            if attempt < cfg.SB_RETRY_COUNT:
                continue
            _increment(SB_FAILCOUNT, fail_lock, loop)
            logger.error(
                "%s/%s, Burst %s : Failure %s/%s, Recipients refused",
                number,
                cfg.SB_TOTAL,
                burst,
                SB_FAILCOUNT.value,
                cfg.SB_STOPFQNT,
            )
        except smtplib.SMTPDataError:
            if attempt < cfg.SB_RETRY_COUNT:
                continue
            _increment(SB_FAILCOUNT, fail_lock, loop)
            logger.error(
                "%s/%s, Burst %s : Failure %s/%s, Data Error",
                number,
                cfg.SB_TOTAL,
                burst,
                SB_FAILCOUNT.value,
                cfg.SB_STOPFQNT,
            )
        except smtplib.SMTPException:
            if attempt < cfg.SB_RETRY_COUNT:
                continue
            _increment(SB_FAILCOUNT, fail_lock, loop)
            logger.error(
                "%s/%s, Burst %s/%s : Failure %s/%s, Unable to send email",
                number,
                cfg.SB_TOTAL,
                burst,
                cfg.SB_BURSTS,
                SB_FAILCOUNT.value,
                cfg.SB_STOPFQNT,
            )


async def async_sendmail(*args, fail_lock: asyncio.Lock | None = None, **kwargs):
    loop = asyncio.get_running_loop()
    await asyncio.to_thread(sendmail, *args, **kwargs, fail_lock=fail_lock, loop=loop)


def parse_server(server: str) -> Tuple[str, int]:
    default_port = 25
    if not server:
        raise ValueError("Server must not be empty")

    if server.count(":") >= 2 and not server.startswith("["):
        host_part, _, tail = server.rpartition(":")
        if tail.isdigit():
            try:
                ipaddress.ip_address(host_part)
            except ValueError:
                try:
                    ipaddress.ip_address(server)
                except ValueError:
                    raise ValueError(
                        (
                            f"Invalid server '{server}': IPv6 addresses with ports "
                            "must be enclosed in '[' and ']'"
                        )
                    ) from None
                else:
                    return server, default_port
            else:
                raise ValueError(
                    (
                        f"Invalid server '{server}': IPv6 addresses with ports "
                        "must be enclosed in '[' and ']'"
                    )
                ) from None
        else:
            try:
                ipaddress.ip_address(server)
            except ValueError:
                raise ValueError(f"Invalid server '{server}'") from None
            else:
                return server, default_port

    try:
        parts = urlsplit(f"//{server}", allow_fragments=False)
    except ValueError as exc:
        raise ValueError(f"Invalid server '{server}': {exc}") from None

    host = parts.hostname
    if host is None:
        raise ValueError(f"Invalid server '{server}")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError(f"Invalid port in server '{server}': {exc}") from None
    if port is None:
        port = default_port
    return host, port
