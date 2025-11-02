from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Optional

from ..config import Config
from .core import _increment, async_throttle, parse_server
from .message import append_message

logger = logging.getLogger(__name__)


class _HostPool:
    def __init__(self, host: str, port: int, max_size: int) -> None:
        self.host = host
        self.port = port
        self.max_size = max_size
        self._available: asyncio.LifoQueue = asyncio.LifoQueue(maxsize=max_size)
        self._semaphore = asyncio.Semaphore(max_size)
        self._warm_lock = asyncio.Lock()

    async def warm(self, cfg: Config) -> None:
        async with self._warm_lock:
            if self._available.qsize() >= self.max_size:
                return
            to_create = self.max_size - self._available.qsize()
            clients = [
                await _create_client(cfg, self.host, self.port)
                for _ in range(to_create)
            ]
            for client in clients:
                self._available.put_nowait(client)

    async def acquire(self, cfg: Config):
        await self._semaphore.acquire()
        try:
            while True:
                try:
                    client = self._available.get_nowait()
                except asyncio.QueueEmpty:
                    client = await _create_client(cfg, self.host, self.port)
                    return client
                else:
                    if getattr(client, "is_connected", True):
                        return client
                    await _safe_quit(client)
        except Exception:
            self._semaphore.release()
            raise

    async def release(self, client) -> None:
        try:
            if getattr(client, "is_connected", True):
                self._available.put_nowait(client)
            else:
                await _safe_quit(client)
        except asyncio.QueueFull:
            await _safe_quit(client)
        finally:
            self._semaphore.release()

    async def discard(self, client) -> None:
        try:
            await _safe_quit(client)
        finally:
            self._semaphore.release()

    async def close(self) -> None:
        while not self._available.empty():
            client = await self._available.get()
            await _safe_quit(client)


_HOST_POOLS: dict[tuple[str, int], _HostPool] = {}
_POOL_LOCK = asyncio.Lock()


async def _safe_quit(client) -> None:
    try:
        await client.quit()
    except Exception:
        pass


def _require_aiosmtplib() -> None:
    try:
        import aiosmtplib  # noqa: F401
    except Exception as exc:  # pragma: no cover - import guard
        raise RuntimeError("aiosmtplib is required for async sending") from exc


async def _create_client(cfg: Config, host: str, port: int):
    import aiosmtplib

    client_kwargs = {
        "hostname": host,
        "port": port,
        "timeout": cfg.SB_TIMEOUT,
    }
    if cfg.SB_SSL:
        client_kwargs["use_tls"] = True

    client = aiosmtplib.SMTP(**client_kwargs)
    await client.connect()
    if cfg.SB_STARTTLS and not cfg.SB_SSL:
        await client.starttls()
    if cfg.SB_HELO_HOST:
        await client.ehlo(cfg.SB_HELO_HOST)
    else:
        await client.ehlo()
    return client


async def _reset_pool(host: str, port: int) -> None:
    key = (host, port)
    async with _POOL_LOCK:
        pool = _HOST_POOLS.pop(key, None)
    if pool:
        await pool.close()


async def _get_pool(cfg: Config, host: str, port: int) -> _HostPool:
    key = (host, port)
    to_close: _HostPool | None = None
    async with _POOL_LOCK:
        pool = _HOST_POOLS.get(key)
        max_size = max(1, int(getattr(cfg, "SB_ASYNC_POOL_SIZE", 1)))
        if pool is None or pool.max_size != max_size:
            if pool is not None:
                to_close = pool
            pool = _HostPool(host, port, max_size)
            _HOST_POOLS[key] = pool
    if to_close is not None:
        await to_close.close()
    return pool


async def reset_async_pools() -> None:
    async with _POOL_LOCK:
        items = list(_HOST_POOLS.items())
        _HOST_POOLS.clear()
    for _, pool in items:
        await pool.close()


async def _async_sendmail_native(
    number: int,
    burst: int,
    SB_FAILCOUNT,
    SB_MESSAGE: bytes,
    cfg: Config,
    *,
    host: str,
    port: int,
    pool: _HostPool | None,
) -> None:
    if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
        return

    attempts = int(getattr(cfg, "SB_RETRY_COUNT", 0)) + 1
    base = 0.2
    for attempt in range(attempts):
        client = None
        try:
            await async_throttle(cfg)
            client = (
                await pool.acquire(cfg)
                if pool
                else await _create_client(cfg, host, port)
            )
            start_t = time.monotonic()
            await client.sendmail(cfg.SB_SENDER, cfg.SB_RECEIVERS, SB_MESSAGE)
            latency = time.monotonic() - start_t
            if latency > cfg.SB_TARPIT_THRESHOLD:
                logger.warning("Possible tarpit detected: %.2fs latency", latency)
            if pool:
                await pool.release(client)
            else:
                await _safe_quit(client)
            logger.info("%s/%s, Burst %s : Email Sent", number, cfg.SB_TOTAL, burst)
            return
        except Exception:
            if pool and client is not None:
                await pool.discard(client)
            elif client is not None:
                await _safe_quit(client)
            if attempt < attempts - 1:
                delay = base * (2**attempt)
                jitter = random.uniform(0, delay)
                await asyncio.sleep(delay + jitter)
                continue
            _increment(SB_FAILCOUNT)


async def _async_bombing_mode_native(
    cfg: Config, attachments: Optional[list[str]] = None
) -> None:
    _require_aiosmtplib()

    host, port = parse_server(cfg.SB_SERVER)
    if getattr(cfg, "SB_ASYNC_REUSE", True):
        if getattr(cfg, "SB_ASYNC_COLD_START", False):
            await _reset_pool(host, port)
        pool = await _get_pool(cfg, host, port)
        if getattr(cfg, "SB_ASYNC_WARM_START", False):
            await pool.warm(cfg)
    else:
        pool = None

    message = append_message(cfg, attachments)
    fail_count = type("C", (), {"value": 0})()

    concurrency = max(1, int(getattr(cfg, "SB_ASYNC_CONCURRENCY", 100)))
    sem = asyncio.Semaphore(concurrency)

    async def worker(number: int, burst: int) -> None:
        if fail_count.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
            return
        async with sem:
            await _async_sendmail_native(
                number,
                burst,
                fail_count,
                message,
                cfg,
                host=host,
                port=port,
                pool=pool,
            )

    for b in range(cfg.SB_BURSTS):
        numbers = range(1, cfg.SB_SGEMAILS + 1)
        tasks = [
            asyncio.create_task(worker(number + (b * cfg.SB_SGEMAILS), b + 1))
            for number in numbers
        ]
        if tasks:
            await asyncio.gather(*tasks)
        await async_throttle(cfg, cfg.SB_BURSTSPSEC)
