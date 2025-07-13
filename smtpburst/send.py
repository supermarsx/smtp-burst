import smtplib
import socket  # noqa: F401 - used by tests for monkeypatching
import time
import sys
import logging
from smtplib import (
    SMTPException,
    SMTPSenderRefused,
    SMTPRecipientsRefused,
    SMTPDataError,
)
from typing import Tuple, List, Optional
from email.message import EmailMessage
import mimetypes
from pathlib import Path

from .config import Config
from . import datagen
from . import attacks

logger = logging.getLogger(__name__)


def throttle(cfg: Config, delay: float = 0.0) -> None:
    """Sleep for ``delay`` seconds plus any global delay."""
    total = cfg.SB_GLOBAL_DELAY + delay
    if total > 0:
        time.sleep(total)


def append_message(cfg: Config, attachments: Optional[List[str]] = None) -> bytes:
    """Construct the message using config values and append random data.

    Message creation always uses :class:`email.message.EmailMessage`.  When
    ``attachments`` are provided they are included as additional parts.
    """
    receivers = ", ".join(cfg.SB_RECEIVERS)
    body = cfg.SB_BODY
    if cfg.SB_TEST_CONTROL:
        body = "\x01\x02" + body
    if cfg.SB_TEMPLATE:
        body = cfg.SB_TEMPLATE.format(
            sender=cfg.SB_SENDER,
            receiver=receivers,
            subject=cfg.SB_SUBJECT,
        )

    rand = datagen.generate(
        cfg.SB_SIZE,
        mode=datagen.DataMode(cfg.SB_DATA_MODE),
        secure=cfg.SB_SECURE_RANDOM,
        words=cfg.SB_DICT_WORDS,
        repeat=cfg.SB_REPEAT_STRING,
        stream=cfg.SB_RAND_STREAM,
    )
    encoding = "utf-7" if cfg.SB_TEST_UTF7 else "utf-8"
    payload = body.encode(encoding) + b"\n\n" + rand

    msg = EmailMessage()
    if cfg.SB_TEST_UNICODE:
        msg["FrOm"] = cfg.SB_SENDER
        msg["tO"] = receivers
    else:
        msg["From"] = cfg.SB_SENDER
        msg["To"] = receivers
    msg["Subject"] = cfg.SB_SUBJECT
    if cfg.SB_TEST_TUNNEL:
        msg["X-Orig"] = "overlap"

    msg.set_content(payload, maintype="text", subtype="plain", cte="8bit")

    if attachments:
        for path in attachments:
            data = Path(path).read_bytes()
            ctype, _ = mimetypes.guess_type(path)
            if ctype:
                maintype, subtype = ctype.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"
            msg.add_attachment(
                data,
                maintype=maintype,
                subtype=subtype,
                filename=Path(path).name,
            )

    return msg.as_bytes()


def sizeof_fmt(num: int, suffix: str = "B") -> str:
    """Return human readable file size."""
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, "Yi", suffix)


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

    logger.info("%s/%s, Burst %s : Sending Email", number, cfg.SB_TOTAL, burst)
    host, port = parse_server(server)
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    if proxy:
        try:  # pragma: no cover - depends on PySocks
            import socks

            ph, pp = parse_server(proxy)

            class ProxySMTP(smtp_cls):
                """SMTP subclass creating connections via a SOCKS proxy."""

                def _get_socket(self, host, port, timeout):
                    if timeout is not None and not timeout:
                        raise ValueError(
                            "Non-blocking socket (timeout=0) is not supported"
                        )
                    if self.debuglevel > 0:
                        self._print_debug(
                            "connect: to",
                            (host, port),
                            self.source_address,
                        )
                    sock = socks.socksocket()
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
    throttle(cfg)
    try:
        with smtp_cls(host, port, timeout=cfg.SB_TIMEOUT) as smtpObj:
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
            start_t = time.monotonic()
            smtpObj.sendmail(cfg.SB_SENDER, cfg.SB_RECEIVERS, SB_MESSAGE)
            latency = time.monotonic() - start_t
            if latency > cfg.SB_TARPIT_THRESHOLD:
                logger.warning("Possible tarpit detected: %.2fs latency", latency)
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


def parse_server(server: str) -> Tuple[str, int]:
    """Return ``(host, port)`` parsed from ``server`` string."""
    if server.startswith("["):
        end = server.find("]")
        if end != -1:
            host = server[1:end]
            rest = server[end + 1 :]
        else:
            host = server[1:]
            rest = ""
        if rest.startswith(":"):
            port_str = rest[1:]
            try:
                port = int(port_str)
            except ValueError:
                port = 25
        else:
            port = 25
    elif ":" in server:
        if server.count(":") > 1 and not server.startswith("["):
            host = server
            port = 25
        else:
            host, port_str = server.rsplit(":", 1)
            try:
                port = int(port_str)
            except ValueError:
                port = 25
    else:
        host = server
        port = 25
    return host, port


def open_sockets(
    host: str,
    count: int,
    port: int = 25,
    cfg: Config | None = None,
    *,
    duration: float | None = None,
    iterations: int | None = None,
) -> None:
    """Delegate to :mod:`smtpburst.attacks` implementation."""
    delay = cfg.SB_OPEN_SOCKETS_DELAY if cfg else 1.0
    timeout = cfg.SB_TIMEOUT if cfg else 10.0
    return attacks.open_sockets(
        host,
        count,
        port,
        delay,
        cfg,
        duration=duration,
        iterations=iterations,
        timeout=timeout,
    )


def _attempt_auth(
    host: str,
    port: int,
    smtp_cls,
    mech: str,
    user: str,
    pwd: str,
    start_tls: bool,
    timeout: float,
) -> bool:
    """Try authenticating ``user``/``pwd`` using ``mech`` and return success."""

    auth_attr = "auth_" + mech.lower().replace("-", "_")
    try:
        with smtp_cls(host, port, timeout=timeout) as sm:
            if start_tls:
                sm.starttls()
            sm.ehlo()
            sm.user, sm.password = user, pwd
            try:
                auth_func = getattr(sm, auth_attr)
            except AttributeError:
                logger.info("Authentication mechanism %s unsupported", mech)
                return False
            sm.auth(mech, auth_func)
        return True
    except smtplib.SMTPAuthenticationError:
        return False


def _smtp_authenticate(
    cfg: Config,
    users: List[str],
    passwords: List[str],
) -> dict[str, bool]:
    """Try authentication attempts for ``users``/``passwords`` and return results."""

    host, port = parse_server(cfg.SB_SERVER)
    smtp_cls = smtplib.SMTP_SSL if cfg.SB_SSL else smtplib.SMTP
    with smtp_cls(host, port, timeout=cfg.SB_TIMEOUT) as smtp:
        if cfg.SB_STARTTLS and not cfg.SB_SSL:
            smtp.starttls()
        smtp.ehlo()
        methods = smtp.esmtp_features.get("auth", "").split()

    results: dict[str, bool] = {}
    for mech in methods:
        success = False
        use_tls = cfg.SB_STARTTLS and not cfg.SB_SSL
        for user in users:
            for pwd in passwords:
                try:
                    success = _attempt_auth(
                        host,
                        port,
                        smtp_cls,
                        mech,
                        user,
                        pwd,
                        use_tls,
                        cfg.SB_TIMEOUT,
                    )
                    if success:
                        logger.info("Auth %s success: %s:%s", mech, user, pwd)
                        break
                except smtplib.SMTPException:
                    break
            if success:
                break
        results[mech] = success
        logger.info(
            "Authentication %s %s", mech, "succeeded" if success else "failed"
        )

    return results


def login_test(cfg: Config) -> dict[str, bool]:
    """Attempt SMTP AUTH logins using wordlists.

    Returns a mapping of mechanism name to success status.
    """

    return _smtp_authenticate(cfg, cfg.SB_USERLIST, cfg.SB_PASSLIST)


def auth_test(cfg: Config) -> dict[str, bool]:
    """Attempt authentication with provided credentials for each advertised
    method.

    Returns a mapping of mechanism name to success status.
    """

    if not cfg.SB_USERNAME or not cfg.SB_PASSWORD:
        return {}

    host, port = parse_server(cfg.SB_SERVER)
    smtp_cls = smtplib.SMTP_SSL if cfg.SB_SSL else smtplib.SMTP
    with smtp_cls(host, port, timeout=cfg.SB_TIMEOUT) as smtp:
        if cfg.SB_STARTTLS and not cfg.SB_SSL:
            smtp.starttls()
        smtp.ehlo()
        methods = smtp.esmtp_features.get("auth", "").split()

    results: dict[str, bool] = {}
    for mech in methods:
        use_tls = cfg.SB_STARTTLS and not cfg.SB_SSL
        try:
            success = _attempt_auth(
                host,
                port,
                smtp_cls,
                mech,
                cfg.SB_USERNAME,
                cfg.SB_PASSWORD,
                use_tls,
                cfg.SB_TIMEOUT,
            )
            logging.getLogger(__name__).info(
                "Authentication %s %s",
                mech,
                "succeeded" if success else "failed",
            )
            results[mech] = success
        except smtplib.SMTPException:
            logging.getLogger(__name__).info(
                "Authentication %s failed", mech
            )
            results[mech] = False
    return results


def send_test_email(cfg: Config) -> None:
    """Send a single minimal email using ``sendmail`` helper."""

    class Counter:
        def __init__(self):
            self.value = 0

    msg = (
        f"From: {cfg.SB_SENDER}\n"
        f"To: {', '.join(cfg.SB_RECEIVERS)}\n"
        f"Subject: {cfg.SB_SUBJECT}\n\n"
        "smtp-burst outbound test\n"
    ).encode("utf-8")

    sendmail(
        1,
        1,
        Counter(),
        msg,
        cfg,
    )


def bombing_mode(cfg: Config, attachments: Optional[List[str]] = None) -> None:
    """Run burst sending autonomously using provided configuration."""
    from multiprocessing import Manager, Process

    logger.info("Generating %s of data to append to message", sizeof_fmt(cfg.SB_SIZE))
    manager = Manager()
    fail_count = manager.Value("i", 0)
    message = append_message(cfg, attachments)
    logger.info("Message using %s of random data", sizeof_fmt(sys.getsizeof(message)))

    for b in range(cfg.SB_BURSTS):
        if cfg.SB_PER_BURST_DATA:
            message = append_message(cfg, attachments)
        numbers = range(1, cfg.SB_SGEMAILS + 1)
        procs = []
        if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
            break
        for number in numbers:
            if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
                break
            throttle(cfg, cfg.SB_SGEMAILSPSEC)
            proxy = None
            if cfg.SB_PROXIES:
                from . import proxy as proxy_util

                idx = number + (b * cfg.SB_SGEMAILS) - 1
                proxy = proxy_util.select_proxy(
                    cfg.SB_PROXIES, cfg.SB_PROXY_ORDER, idx
                )
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
                    "server": cfg.SB_SERVER,
                    "proxy": proxy,
                    "users": cfg.SB_USERLIST,
                    "passwords": cfg.SB_PASSLIST,
                },
            )
            procs.append(proc)
            proc.start()
        for proc in procs:
            proc.join()
        throttle(cfg, cfg.SB_BURSTSPSEC)

    if cfg.SB_RAND_STREAM:
        try:
            cfg.SB_RAND_STREAM.close()
        except Exception:
            pass
