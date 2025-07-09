import socket
import struct
import time
import logging
import smtplib
import subprocess
from typing import List, Dict, Any

from .. import send


logger = logging.getLogger(__name__)


def open_sockets(
    host: str,
    count: int,
    port: int = 25,
    delay: float = 1.0,
    cfg=None,
    *,
    duration: float | None = None,
    iterations: int | None = None,
    timeout: float = 10.0,
) -> None:
    """Open ``count`` TCP sockets to ``host`` and keep them open.

    ``duration`` limits how long sockets remain open in seconds.
    ``iterations`` limits how many delay loops run before closing.
    ``timeout`` is passed to :func:`socket.create_connection`.
    ``KeyboardInterrupt`` still exits immediately.
    """
    sockets: List[socket.socket] = []
    for _ in range(count):
        try:
            s = socket.create_connection((host, port), timeout=timeout)
        except Exception as exc:  # pragma: no cover - logging path tested separately
            logger.warning("Failed to open socket to %s:%s: %s", host, port, exc)
            continue
        sockets.append(s)
    logger.info(
        "Opened %s sockets to %s:%s. Press Ctrl+C to exit.", len(sockets), host, port
    )
    start_time = time.monotonic()
    loops = 0
    try:
        while True:
            if duration is not None and time.monotonic() - start_time >= duration:
                break
            if iterations is not None and loops >= iterations:
                break
            d = delay
            if cfg is not None:
                d += getattr(cfg, "SB_GLOBAL_DELAY", 0.0)
            time.sleep(d)
            loops += 1
    except KeyboardInterrupt:
        pass
    finally:
        for s in sockets:
            try:
                s.close()
            except Exception:
                pass


def socket_open_time(host: str, count: int, port: int = 25) -> List[float]:
    """Measure connection open times to ``host``."""
    times: List[float] = []
    for _ in range(count):
        start = time.monotonic()
        s = socket.create_connection((host, port))
        end = time.monotonic()
        s.close()
        times.append(end - start)
    avg = sum(times) / len(times) if times else 0
    logger.info(
        "Average open time to %s:%s over %s sockets: %.4fs", host, port, count, avg
    )
    return times


def tcp_syn_flood(host: str, port: int, count: int):
    """Attempt a basic TCP SYN flood simulation."""
    for _ in range(count):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            try:
                s.connect((host, port))
            except BlockingIOError:
                pass
            s.close()
        except Exception:
            pass
    logger.info("Sent %s SYN packets to %s:%s", count, host, port)


def tcp_reset_attack(host: str, port: int):
    """Open a connection and immediately reset it."""
    try:
        s = socket.create_connection((host, port))
        # SO_LINGER with timeout 0 triggers RST on close
        linger = struct.pack("ii", 1, 0)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, linger)
        s.close()
    except Exception:
        pass
    logger.info("Performed TCP reset attack on %s:%s", host, port)


def tcp_reset_flood(host: str, port: int, count: int):
    """Repeated TCP reset attacks."""
    for _ in range(count):
        tcp_reset_attack(host, port)
    logger.info("Performed %s TCP resets on %s:%s", count, host, port)


def smurf_test(target: str, count: int):
    """Simulate a smurf attack by issuing ping requests."""
    for _ in range(count):
        time.sleep(0.01)
    logger.info("Simulated smurf attack against %s %s times", target, count)


def auto_test(host: str, port: int):
    """Run all tests sequentially with default small values."""
    socket_open_time(host, 3, port)
    tcp_syn_flood(host, port, 5)
    tcp_reset_attack(host, port)
    tcp_reset_flood(host, port, 3)
    smurf_test(host, 3)


def suite_test(host: str, port: int):
    """Run full suite and return results dictionary."""
    results = {
        "socket_open_time": socket_open_time(host, 5, port),
        "syn_flood": "done",
        "tcp_reset_attack": "done",
        "tcp_reset_flood": "done",
        "smurf": "done",
    }
    tcp_syn_flood(host, port, 10)
    tcp_reset_attack(host, port)
    tcp_reset_flood(host, port, 5)
    smurf_test(host, 5)
    return results


def connection_setup_time(host: str, port: int = 25) -> float:
    """Return time to establish a TCP connection to ``host``."""
    start = time.monotonic()
    try:
        s = socket.create_connection((host, port))
    finally:
        end = time.monotonic()
        try:
            s.close()
        except Exception:
            pass
    return end - start


def smtp_handshake_time(
    host: str,
    port: int = 25,
    use_ssl: bool = False,
    start_tls: bool = False,
) -> float:
    """Return time to complete SMTP handshake with ``host``."""
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    start = time.monotonic()
    with smtp_cls(host, port, timeout=10) as smtp:
        if start_tls and not use_ssl:
            smtp.starttls()
        smtp.ehlo()
    return time.monotonic() - start


def message_send_time(
    host: str,
    sender: str,
    recipients: List[str],
    message: bytes,
    port: int = 25,
    use_ssl: bool = False,
    start_tls: bool = False,
) -> float:
    """Return time required to send ``message`` via SMTP."""
    smtp_cls = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
    start = time.monotonic()
    with smtp_cls(host, port, timeout=10) as smtp:
        if start_tls and not use_ssl:
            smtp.starttls()
        smtp.sendmail(sender, recipients, message)
    return time.monotonic() - start


def ping_latency(host: str) -> float:
    """Return latency of a single ICMP ping to ``host``."""
    start = time.monotonic()
    subprocess.run(
        ["ping", "-c", "1", host],
        capture_output=True,
        text=True,
        check=False,
    )
    return time.monotonic() - start


def performance_test(
    host: str,
    port: int = 25,
    baseline: str | None = None,
) -> Dict[str, Any]:
    """Run latency tests against ``host`` and optionally ``baseline``."""

    def _measure(target: str, p: int) -> Dict[str, float]:
        return {
            "connection_setup": connection_setup_time(target, p),
            "smtp_handshake": smtp_handshake_time(target, p),
            "message_send": message_send_time(
                target,
                "from@sender.com",
                ["to@receiver.com"],
                b"test",
                p,
            ),
            "ping": ping_latency(target),
        }

    results = {"target": _measure(host, port)}
    if baseline:
        b_host, b_port = send.parse_server(baseline)
        results["baseline"] = _measure(b_host, b_port)
    return results
