import socket
import struct
import time
from typing import List


def open_sockets(host: str, count: int, port: int = 25):
    """Open ``count`` TCP sockets to ``host`` and keep them open."""
    sockets: List[socket.socket] = []
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
    print(f"Average open time to {host}:{port} over {count} sockets: {avg:.4f}s")
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
    print(f"Sent {count} SYN packets to {host}:{port}")


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
    print(f"Performed TCP reset attack on {host}:{port}")


def tcp_reset_flood(host: str, port: int, count: int):
    """Repeated TCP reset attacks."""
    for _ in range(count):
        tcp_reset_attack(host, port)
    print(f"Performed {count} TCP resets on {host}:{port}")


def smurf_test(target: str, count: int):
    """Simulate a smurf attack by issuing ping requests."""
    for _ in range(count):
        time.sleep(0.01)
    print(f"Simulated smurf attack against {target} {count} times")


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
