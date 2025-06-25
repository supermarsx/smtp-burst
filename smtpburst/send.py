import smtplib
import socket
import time
from smtplib import (
    SMTPException,
    SMTPSenderRefused,
    SMTPRecipientsRefused,
    SMTPDataError,
)
from typing import Tuple

from . import config, datagen
from . import attacks


def appendMessage() -> bytes:
    """Construct the message using config values and append random data."""
    receivers = ", ".join(config.SB_RECEIVERS)
    base = (
        f"From: {config.SB_SENDER}\n"
        f"To: {receivers}\n"
        f"Subject: {config.SB_SUBJECT}\n\n"
        f"{config.SB_BODY}\n\n"
    )
    rand = datagen.generate(
        config.SB_SIZE,
        mode=config.SB_DATA_MODE,
        secure=config.SB_SECURE_RANDOM,
        words=config.SB_DICT_WORDS,
        repeat=config.SB_REPEAT_STRING,
        stream=config.SB_RAND_STREAM,
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
    server: str = config.SB_SERVER,
    proxy: str | None = None,
    users=None,
    passwords=None,
    use_ssl: bool = False,
    start_tls: bool = False,
):
    """Send a single email if failure threshold not reached.

    Parameters ``use_ssl`` and ``start_tls`` control the connection security.
    """
    if SB_FAILCOUNT.value >= config.SB_STOPFQNT and config.SB_STOPFAIL:
        return

    print(f"{number}/{config.SB_TOTAL}, Burst {burst} : Sending Email")
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
                            print(f"Auth success: {user}:{pwd}")
                            success = True
                            break
                        except SMTPException:
                            continue
                    if success:
                        break
            smtpObj.sendmail(config.SB_SENDER, config.SB_RECEIVERS, SB_MESSAGE)
        print(f"{number}/{config.SB_TOTAL}, Burst {burst} : Email Sent")
    except SMTPException:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{config.SB_TOTAL}, Burst {burst}/{config.SB_BURSTS} : Failure {SB_FAILCOUNT.value}/{config.SB_STOPFQNT}, Unable to send email"
        )
    except SMTPSenderRefused:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{config.SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{config.SB_STOPFQNT}, Sender refused"
        )
    except SMTPRecipientsRefused:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{config.SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{config.SB_STOPFQNT}, Recipients refused"
        )
    except SMTPDataError:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{config.SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{config.SB_STOPFQNT}, Data Error"
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
