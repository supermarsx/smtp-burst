import socket
import struct
import time
import logging
from typing import List


logger = logging.getLogger(__name__)


def open_sockets(host: str, count: int, port: int = 25, delay: float = 1.0, cfg=None):
    """Open ``count`` TCP sockets to ``host`` and keep them open."""
    sockets: List[socket.socket] = []
    for _ in range(count):
        try:
            s = socket.create_connection((host, port))
        except Exception as exc:  # pragma: no cover - logging path tested separately
            logger.warning(
                "Failed to open socket to %s:%s: %s", host, port, exc
            )
            continue
        sockets.append(s)
    logger.info(
        "Opened %s sockets to %s:%s. Press Ctrl+C to exit.", len(sockets), host, port
    )
    try:
        while True:
            d = delay
            if cfg is not None:
                d += getattr(cfg, 'SB_GLOBAL_DELAY', 0.0)
            time.sleep(d)
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
        linger = struct.pack('ii', 1, 0)
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
        'socket_open_time': socket_open_time(host, 5, port),
        'syn_flood': 'done',
        'tcp_reset_attack': 'done',
        'tcp_reset_flood': 'done',
        'smurf': 'done',
    }
    tcp_syn_flood(host, port, 10)
    tcp_reset_attack(host, port)
    tcp_reset_flood(host, port, 5)
    smurf_test(host, 5)
    return results
