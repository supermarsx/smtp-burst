from __future__ import annotations
import logging
import sys
import time
from typing import Optional
from ..config import Config
from .core import throttle

logger = logging.getLogger(__name__)


def send_test_email(cfg: Config) -> None:
    class Counter:
        def __init__(self):
            self.value = 0

    msg = (
        f"From: {cfg.SB_SENDER}\n"
        f"To: {', '.join(cfg.SB_RECEIVERS)}\n"
        f"Subject: {cfg.SB_SUBJECT}\n\n"
        "smtp-burst outbound test\n"
    ).encode("utf-8")

    # Import at call time so tests can monkeypatch send.sendmail
    from . import sendmail

    sendmail(1, 1, Counter(), msg, cfg)


def bombing_mode(cfg: Config, attachments: Optional[list[str]] = None) -> None:
    from multiprocessing import Manager
    from .core import sendmail  # noqa: F401
    from .. import proxy as proxy_util

    from . import sizeof_fmt, append_message

    logger.info("Generating %s of data to append to message", sizeof_fmt(cfg.SB_SIZE))
    manager = Manager()
    fail_count = manager.Value("i", 0)
    message = append_message(cfg, attachments)
    logger.info("Message using %s of random data", sizeof_fmt(sys.getsizeof(message)))

    start_budget = time.monotonic()
    from . import ProcessPoolExecutor  # use package-level symbol for tests

    with ProcessPoolExecutor(max_workers=cfg.SB_SGEMAILS) as pool:
        for b in range(cfg.SB_BURSTS):
            if cfg.SB_PER_BURST_DATA:
                message = append_message(cfg, attachments)
            numbers = range(1, cfg.SB_SGEMAILS + 1)
            futures = []
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
                throttle(cfg, cfg.SB_SGEMAILSPSEC)
                proxy = None
                if cfg.SB_PROXIES:
                    idx = number + (b * cfg.SB_SGEMAILS) - 1
                    proxy = proxy_util.select_proxy(
                        cfg.SB_PROXIES, cfg.SB_PROXY_ORDER, idx
                    )
                # Import sendmail at call-time to honor test monkeypatches
                from . import sendmail as _sendmail

                futures.append(
                    pool.submit(
                        _sendmail,
                        number + (b * cfg.SB_SGEMAILS),
                        b + 1,
                        fail_count,
                        message,
                        cfg,
                        server=cfg.SB_SERVER,
                        proxy=proxy,
                        users=cfg.SB_USERLIST,
                        passwords=cfg.SB_PASSLIST,
                    )
                )
            for fut in futures:
                fut.result()
            throttle(cfg, cfg.SB_BURSTSPSEC)

    if cfg.SB_RAND_STREAM:
        try:
            cfg.SB_RAND_STREAM.close()
        except Exception:
            pass


from .async_mode import async_bombing_mode  # noqa: E402, F401
