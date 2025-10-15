from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import List, Optional

from ..config import Config
from .core import async_throttle

logger = logging.getLogger(__name__)


async def async_bombing_mode(
    cfg: Config, attachments: Optional[List[str]] = None
) -> None:
    if getattr(cfg, "SB_ASYNC_NATIVE", False):
        from .native import _async_bombing_mode_native

        await _async_bombing_mode_native(cfg, attachments)
        return

    from . import sizeof_fmt, append_message

    logger.info("Generating %s of data to append to message", sizeof_fmt(cfg.SB_SIZE))

    class Counter:
        def __init__(self):
            self.value = 0

    fail_count = Counter()
    fail_lock = asyncio.Lock()
    message = append_message(cfg, attachments)
    logger.info("Message using %s of random data", sizeof_fmt(sys.getsizeof(message)))

    start_budget = time.monotonic()
    for b in range(cfg.SB_BURSTS):
        if cfg.SB_PER_BURST_DATA:
            message = append_message(cfg, attachments)
        numbers = range(1, cfg.SB_SGEMAILS + 1)
        tasks = []
        if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
            break
        for number in numbers:
            if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
                break
            if (
                cfg.SB_BUDGET_SECONDS
                and (time.monotonic() - start_budget) >= cfg.SB_BUDGET_SECONDS
            ):
                logger.info("Time budget reached; stopping sends")
                break
            await async_throttle(cfg, cfg.SB_SGEMAILSPSEC)
            # Import sendmail lazily to allow test monkeypatch
            from . import sendmail as _sendmail

            async def _runner(n, brst):
                await asyncio.to_thread(
                    _sendmail,
                    n,
                    brst,
                    fail_count,
                    message,
                    cfg,
                    server=cfg.SB_SERVER,
                    users=cfg.SB_USERLIST,
                    passwords=cfg.SB_PASSLIST,
                    fail_lock=fail_lock,
                )

            tasks.append(
                asyncio.create_task(_runner(number + (b * cfg.SB_SGEMAILS), b + 1))
            )
        if tasks:
            await asyncio.gather(*tasks)
        await async_throttle(cfg, cfg.SB_BURSTSPSEC)

    if cfg.SB_RAND_STREAM:
        try:
            cfg.SB_RAND_STREAM.close()
        except Exception:
            pass
