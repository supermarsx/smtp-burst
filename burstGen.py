import random
import smtplib
from smtplib import *
from contextlib import contextmanager
import sys

from burstVars import *
try:
    import socks  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    socks = None

# Generate random data
# size      integer, size in bytes
def genData(size):
    return bytearray(random.getrandbits(8) for i in range(size)).decode("utf-8", "ignore")

# Append message with generated data
def appendMessage() :
    return (SB_MESSAGEC + genData(SB_SIZE)).encode('ascii', 'ignore')

# Get human readable size from sizeof
# num       integer, size in bytes
# suffix        string, suffix to append
def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def _parse_hostport(addr, default_port=25):
    """Return (host, port) tuple from a host:port string."""
    if ':' in addr:
        host, port = addr.rsplit(':', 1)
        return host, int(port)
    return addr, default_port


@contextmanager
def open_smtp(server, proxy=None):
    """Context manager returning connected SMTP object."""
    host, port = _parse_hostport(server)
    if proxy:
        if not socks:
            raise RuntimeError('PySocks required for proxy support')
        phost, pport = _parse_hostport(proxy)
        orig_socket = smtplib.socket.socket
        socks.set_default_proxy(socks.SOCKS5, phost, pport)
        smtplib.socket.socket = socks.socksocket
        try:
            smtp = smtplib.SMTP(host, port)
            yield smtp
        finally:
            try:
                smtp.quit()
            except Exception:
                pass
            smtplib.socket.socket = orig_socket
            socks.set_default_proxy(None)
    else:
        smtp = smtplib.SMTP(host, port)
        try:
            yield smtp
        finally:
            try:
                smtp.quit()
            except Exception:
                pass
    
# Send email
# number        integer,    Email number
# burst         integer,    Burst round
# SB_FAILCOUNT  integer,    Current send fail count
# SB_MESSAGE    string,     Message string to send
def sendmail(number, burst, SB_FAILCOUNT, SB_MESSAGE):
    if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL:
        return

    print("%s/%s, Burst %s : Sending Email" % (number, SB_TOTAL, burst))

    proxies = SB_PROXIES or [None]
    start = ((number - 1) % len(SB_PROXIES)) if SB_ROTATE_PROXIES and SB_PROXIES else 0
    for attempt in range(len(proxies)):
        proxy = SB_PROXIES[(start + attempt) % len(SB_PROXIES)] if SB_PROXIES else None
        try:
            with open_smtp(SB_SERVER, proxy) as smtpObj:
                smtpObj.sendmail(SB_SENDER, SB_RECEIVERS, SB_MESSAGE)
            print("%s/%s, Burst %s : Email Sent" % (number, SB_TOTAL, burst))
            return
        except (OSError, SMTPException):
            last_error = sys.exc_info()[1]
            continue
    SB_FAILCOUNT.value += 1
    print("%s/%s, Burst %s/%s : Failure %s/%s, %s" % (
        number,
        SB_TOTAL,
        burst,
        SB_BURSTS,
        SB_FAILCOUNT.value,
        SB_STOPFQNT,
        getattr(last_error, 'strerror', str(last_error)),
    ))
