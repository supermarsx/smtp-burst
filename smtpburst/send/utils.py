from __future__ import annotations

from ..config import Config
from .. import attacks


def open_sockets(
    host: str,
    count: int,
    port: int = 25,
    cfg: Config | None = None,
    *,
    duration: float | None = None,
    iterations: int | None = None,
) -> None:
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
