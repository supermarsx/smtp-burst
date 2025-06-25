import random
import smtplib
import socket
import time
from smtplib import SMTPException, SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError
from typing import Tuple

from .config import Config


def genData(size: int) -> str:
    """Generate random string data of ``size`` bytes."""
    return bytearray(random.getrandbits(8) for _ in range(size)).decode("utf-8", "ignore")


def appendMessage(cfg: Config) -> bytes:
    """Construct the message using ``cfg`` values and append random data."""
    receivers = ", ".join(cfg.receivers)
    base = (
        f"From: {cfg.sender}\n"
        f"To: {receivers}\n"
        f"Subject: {cfg.subject}\n\n"
        f"{cfg.body}\n\n"
    )
    return (base + genData(cfg.size)).encode("ascii", "ignore")


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
    if SB_FAILCOUNT.value >= cfg.stop_fail_count and cfg.stop_on_fail:
        return

    total = cfg.total
    print(f"{number}/{total}, Burst {burst} : Sending Email")
    host, port = parse_server(server or cfg.server)
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
            smtpObj.sendmail(cfg.sender, cfg.receivers, SB_MESSAGE)
        print(f"{number}/{total}, Burst {burst} : Email Sent")
    except SMTPException:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{total}, Burst {burst}/{cfg.bursts} : Failure {SB_FAILCOUNT.value}/{cfg.stop_fail_count}, Unable to send email"
        )
    except SMTPSenderRefused:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{total}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{cfg.stop_fail_count}, Sender refused"
        )
    except SMTPRecipientsRefused:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{total}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{cfg.stop_fail_count}, Recipients refused"
        )
    except SMTPDataError:
        SB_FAILCOUNT.value += 1
        print(
            f"{number}/{total}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{cfg.stop_fail_count}, Data Error"
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
    """Open ``count`` TCP sockets to ``host`` and keep them open."""
    sockets = []
    for _ in range(count):
        s = socket.create_connection((host, port))
        sockets.append(s)
    print(f"Opened {len(sockets)} sockets to {host}:{port}. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for s in sockets:
            try:
                s.close()
            except Exception:
                pass
