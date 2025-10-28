from __future__ import annotations

import asyncio
import time
from typing import Optional

from ..config import Config
from .core import async_throttle, _increment
from .message import append_message
from . import sizeof_fmt  # noqa: F401


async def _async_sendmail_native(
    number: int,
    burst: int,
    SB_FAILCOUNT,
    SB_MESSAGE: bytes,
    cfg: Config,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
) -> None:
    try:
        import aiosmtplib  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        return

    from .core import parse_server

    host, port = parse_server(cfg.SB_SERVER)
    use_ssl = cfg.SB_SSL
    start_tls = cfg.SB_STARTTLS
    if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
        return
    attempts = int(getattr(cfg, "SB_RETRY_COUNT", 0)) + 1
    base = 0.2
    for i in range(attempts):
        try:
            await async_throttle(cfg)
            if use_ssl:
                client = aiosmtplib.SMTP(
                    hostname=host, port=port, timeout=cfg.SB_TIMEOUT, use_tls=True
                )
            else:
                client = aiosmtplib.SMTP(
                    hostname=host, port=port, timeout=cfg.SB_TIMEOUT
                )
            await client.connect()
            if start_tls and not use_ssl:
                await client.starttls()
            if cfg.SB_HELO_HOST:
                await client.ehlo(cfg.SB_HELO_HOST)
            else:
                await client.ehlo()
            start_t = time.monotonic()
            await client.sendmail(cfg.SB_SENDER, cfg.SB_RECEIVERS, SB_MESSAGE)
            latency = time.monotonic() - start_t
            if latency > cfg.SB_TARPIT_THRESHOLD:
                import logging

                logging.getLogger(__name__).warning(
                    "Possible tarpit detected: %.2fs latency", latency
                )
            await client.quit()
            import logging

            logging.getLogger(__name__).info(
                "%s/%s, Burst %s : Email Sent", number, cfg.SB_TOTAL, burst
            )
            return
        except Exception:
            if i < attempts - 1:
                try:
                    await asyncio.sleep(base * (2**i))
                except Exception:
                    pass
                continue
            _increment(SB_FAILCOUNT)


async def _async_bombing_mode_native(
    cfg: Config, attachments: Optional[list[str]] = None
) -> None:
    import asyncio

    sem = asyncio.Semaphore(max(1, int(getattr(cfg, "SB_ASYNC_CONCURRENCY", 100))))
    message = append_message(cfg, attachments)
    fail_count = type("C", (), {"value": 0})()

    try:
        import aiosmtplib  # type: ignore  # noqa: F401
    except Exception:  # pragma: no cover
        return

    async def worker(number: int, burst: int) -> None:
        async with sem:
            await _async_sendmail_native(number, burst, fail_count, message, cfg)

    for b in range(cfg.SB_BURSTS):
        numbers = range(1, cfg.SB_SGEMAILS + 1)
        tasks = [
            asyncio.create_task(worker(number + (b * cfg.SB_SGEMAILS), b + 1))
            for number in numbers
        ]
        if tasks:
            await asyncio.gather(*tasks)
