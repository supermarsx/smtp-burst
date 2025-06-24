import random
import smtplib
import socket
import time
from smtplib import SMTPException, SMTPSenderRefused, SMTPRecipientsRefused, SMTPDataError
from typing import Tuple

from .config import *


def genData(size: int) -> str:
    """Generate random string data of ``size`` bytes."""
    return bytearray(random.getrandbits(8) for _ in range(size)).decode("utf-8", "ignore")


def appendMessage() -> bytes:
    """Return the base message plus random data."""
    return (SB_MESSAGEC + genData(SB_SIZE)).encode('ascii', 'ignore')


def sizeof_fmt(num: int, suffix: str = 'B') -> str:
    """Return human readable file size."""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def sendmail(number: int, burst: int, SB_FAILCOUNT, SB_MESSAGE: bytes):
    """Send a single email if failure threshold not reached."""
    if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL:
        return

    print(f"{number}/{SB_TOTAL}, Burst {burst} : Sending Email")
    try:
        with smtplib.SMTP(SB_SERVER) as smtpObj:
            smtpObj.sendmail(SB_SENDER, SB_RECEIVERS, SB_MESSAGE)
        print(f"{number}/{SB_TOTAL}, Burst {burst} : Email Sent")
    except SMTPException:
        SB_FAILCOUNT.value += 1
        print(f"{number}/{SB_TOTAL}, Burst {burst}/{SB_BURSTS} : Failure {SB_FAILCOUNT.value}/{SB_STOPFQNT}, Unable to send email")
    except SMTPSenderRefused:
        SB_FAILCOUNT.value += 1
        print(f"{number}/{SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{SB_STOPFQNT}, Sender refused")
    except SMTPRecipientsRefused:
        SB_FAILCOUNT.value += 1
        print(f"{number}/{SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{SB_STOPFQNT}, Recipients refused")
    except SMTPDataError:
        SB_FAILCOUNT.value += 1
        print(f"{number}/{SB_TOTAL}, Burst {burst} : Failure {SB_FAILCOUNT.value}/{SB_STOPFQNT}, Data Error")


def parse_server(server: str) -> Tuple[str, int]:
    """Return ``(host, port)`` parsed from ``server`` string."""
    if ":" in server:
        host, port_str = server.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            host = server
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
