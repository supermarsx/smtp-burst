import asyncio
import types

import pytest
import smtpburst.send as send
from smtpburst.config import Config
import logging
import sys


def test_send_test_email(monkeypatch):
    calls = []

    def fake_sendmail(number, burst, counter, msg, cfg, **kwargs):
        calls.append((number, burst, counter.value, msg, cfg, kwargs))

    monkeypatch.setattr(send, "sendmail", fake_sendmail)

    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com", "e@f.com"]
    cfg.SB_SUBJECT = "Subj"

    send.send_test_email(cfg)

    assert len(calls) == 1
    number, burst, counter_val, msg, passed_cfg, kwargs = calls[0]
    expected = (
        f"From: {cfg.SB_SENDER}\n"
        f"To: {', '.join(cfg.SB_RECEIVERS)}\n"
        f"Subject: {cfg.SB_SUBJECT}\n\n"
        "smtp-burst outbound test\n"
    ).encode("utf-8")
    assert msg == expected
    assert passed_cfg is cfg


@pytest.mark.parametrize(
    "server,host,port",
    [
        ("127.0.0.1", "127.0.0.1", 25),
        ("127.0.0.1:2525", "127.0.0.1", 2525),
        ("[2001:db8::1]", "2001:db8::1", 25),
        ("[2001:db8::1]:587", "2001:db8::1", 587),
        ("2001:db8::1", "2001:db8::1", 25),
    ],
)
def test_parse_server_matrix(server, host, port):
    """Verify parse_server with IPv4 and IPv6 variants."""
    assert send.parse_server(server) == (host, port)


@pytest.mark.parametrize(
    "server",
    [
        "bad:port",  # non-numeric port
        "2001:db8::1:587",  # IPv6 with port but missing brackets
        "[2001:db8::1",  # unmatched bracket
    ],
)
def test_parse_server_malformed(server):
    """Malformed server strings should raise ValueError."""
    with pytest.raises(ValueError):
        send.parse_server(server)


def test_append_message_missing_attachment(tmp_path, caplog):
    cfg = Config()
    cfg.SB_SIZE = 0
    missing = tmp_path / "missing.txt"
    with caplog.at_level(logging.WARNING):
        msg = send.append_message(cfg, attachments=[str(missing)])
    assert isinstance(msg, bytes)
    assert str(missing) in caplog.text
    assert missing.name not in msg.decode("utf-8", errors="ignore")


def test_sendmail_retry(monkeypatch):
    class FlakySMTP:
        attempts = 0

        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def sendmail(self, sender, receivers, msg):
            type(self).attempts += 1
            if type(self).attempts == 1:
                raise send.SMTPException("temporary failure")

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", FlakySMTP)

    cfg = Config()
    cfg.SB_RETRY_COUNT = 1
    counter = type("C", (), {"value": 0})()

    send.sendmail(1, 1, counter, b"msg", cfg)

    assert FlakySMTP.attempts == 2
    assert counter.value == 0


@pytest.mark.parametrize("helo_host", ["", "helo.example"])
def test_sendmail_ehlo(monkeypatch, helo_host):
    called = {}

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            called["starttls"] = True

        def ehlo(self, host=None):
            called["ehlo"] = host

        def sendmail(self, sender, receivers, msg):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)

    cfg = Config()
    cfg.SB_HELO_HOST = helo_host
    counter = type("C", (), {"value": 0})()

    send.sendmail(1, 1, counter, b"msg", cfg, use_ssl=False, start_tls=False)

    expected = helo_host or None
    assert called["ehlo"] == expected


def test_sendmail_starttls_ehlo(monkeypatch):
    calls = []

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            calls.append("starttls")

        def ehlo(self, host=None):
            calls.append(("ehlo", host))

        def sendmail(self, sender, receivers, msg):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)

    cfg = Config()
    cfg.SB_HELO_HOST = "helo.example"
    counter = type("C", (), {"value": 0})()

    send.sendmail(1, 1, counter, b"msg", cfg, use_ssl=False, start_tls=True)

    assert calls == [
        ("ehlo", "helo.example"),
        "starttls",
        ("ehlo", "helo.example"),
    ]


def test_append_message_trace_header():
    cfg = Config()
    cfg.SB_SIZE = 0
    cfg.SB_TRACE_ID = "trace-123"
    cfg.SB_TRACE_HEADER = "X-Trace"
    msg = send.append_message(cfg)
    text = msg.decode("utf-8", errors="ignore")
    assert "X-Trace: trace-123" in text


def test_sendmail_proxy_auth(monkeypatch):
    calls = {}

    class DummySock:
        def set_proxy(self, proxy_type, host, port, username=None, password=None):
            calls["args"] = (proxy_type, host, port, username, password)

        def settimeout(self, t):
            pass

        def bind(self, addr):
            pass

        def connect(self, addr):
            pass

    class DummySocksModule:
        SOCKS5 = "socks5"

        def socksocket(self):
            return DummySock()

    monkeypatch.setitem(sys.modules, "socks", DummySocksModule())

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.source_address = None
            self.debuglevel = 0
            self._host = host
            self.context = type(
                "C", (), {"wrap_socket": lambda self, s, server_hostname=None: s}
            )()
            self._get_socket(host, port, timeout)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def _get_socket(self, host, port, timeout):
            return None

        def sendmail(self, sender, receivers, msg):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(send.smtplib, "SMTP_SSL", DummySMTP)

    cfg = Config()
    counter = type("C", (), {"value": 0})()

    send.sendmail(1, 1, counter, b"msg", cfg, proxy="user:pass@h:1", use_ssl=False)

    assert calls["args"] == ("socks5", "h", 1, "user", "pass")


def test_bombing_mode_uses_pool(monkeypatch):
    """bombing_mode should use a persistent worker pool."""

    sent = []

    def fake_sendmail(number, burst, counter, msg, cfg, **kwargs):
        sent.append((number, burst, msg))

    monkeypatch.setattr(send, "sendmail", fake_sendmail)
    monkeypatch.setattr(send, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))

    created = []

    class DummyPool:
        def __init__(self, max_workers=None):
            self.submitted = []
            created.append(self)

        def submit(self, fn, *args, **kwargs):
            self.submitted.append((fn, args, kwargs))

            class DummyFuture:
                def result(self_inner):
                    return fn(*args, **kwargs)

            return DummyFuture()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(send, "ProcessPoolExecutor", DummyPool)

    import multiprocessing

    def boom(*a, **k):  # pragma: no cover - should not be called
        raise AssertionError("Process should not be spawned")

    monkeypatch.setattr(multiprocessing, "Process", boom)

    cfg = Config()
    cfg.SB_SGEMAILS = 1
    cfg.SB_BURSTS = 2
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0

    send.bombing_mode(cfg)

    assert len(created) == 1
    pool = created[0]
    assert len(pool.submitted) == 2
    assert len(sent) == 2
    assert {n for n, b, m in sent} == {1, 2}


def test_async_bombing_mode_reuses_connections(monkeypatch):
    import smtpburst.send.native as native

    asyncio.run(native.reset_async_pools())

    class FakeSMTP:
        instances: list["FakeSMTP"] = []
        connect_calls = 0
        sendmail_calls = 0
        max_inflight = 0
        _inflight = 0

        def __init__(self, hostname, port, timeout=None, use_tls=False):
            self.hostname = hostname
            self.port = port
            self.timeout = timeout
            self.use_tls = use_tls
            self._connected = False
            FakeSMTP.instances.append(self)

        async def connect(self):
            FakeSMTP.connect_calls += 1
            self._connected = True

        async def starttls(self):
            return None

        async def ehlo(self, host=None):
            return None

        async def sendmail(self, sender, receivers, message):
            FakeSMTP._inflight += 1
            FakeSMTP.max_inflight = max(FakeSMTP.max_inflight, FakeSMTP._inflight)
            FakeSMTP.sendmail_calls += 1
            await asyncio.sleep(0)
            FakeSMTP._inflight -= 1

        async def quit(self):
            self._connected = False

        @property
        def is_connected(self):
            return self._connected

    async def immediate_throttle(*args, **kwargs):
        return None

    monkeypatch.setitem(sys.modules, "aiosmtplib", types.SimpleNamespace(SMTP=FakeSMTP))
    monkeypatch.setattr(native, "async_throttle", immediate_throttle)
    monkeypatch.setattr(native, "append_message", lambda cfg, attachments=None: b"msg")

    cfg = Config()
    cfg.SB_SGEMAILS = 2
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    cfg.SB_ASYNC_POOL_SIZE = 1
    cfg.SB_ASYNC_CONCURRENCY = 4

    asyncio.run(send.async_bombing_mode(cfg))

    assert FakeSMTP.connect_calls == 1
    assert FakeSMTP.sendmail_calls == 2
    assert FakeSMTP.max_inflight == 1


def test_async_bombing_mode_warm_start_prefills_pool(monkeypatch):
    import smtpburst.send.native as native

    asyncio.run(native.reset_async_pools())

    class FakeSMTP:
        connect_calls = 0
        instances: list["FakeSMTP"] = []

        def __init__(self, hostname, port, timeout=None, use_tls=False):
            self._connected = False
            FakeSMTP.instances.append(self)

        async def connect(self):
            FakeSMTP.connect_calls += 1
            self._connected = True

        async def starttls(self):
            return None

        async def ehlo(self, host=None):
            return None

        async def sendmail(self, sender, receivers, message):
            return None

        async def quit(self):
            self._connected = False

        @property
        def is_connected(self):
            return self._connected

    async def immediate_throttle(*args, **kwargs):
        return None

    monkeypatch.setitem(sys.modules, "aiosmtplib", types.SimpleNamespace(SMTP=FakeSMTP))
    monkeypatch.setattr(native, "async_throttle", immediate_throttle)
    monkeypatch.setattr(native, "append_message", lambda cfg, attachments=None: b"msg")

    cfg = Config()
    cfg.SB_SGEMAILS = 1
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    cfg.SB_ASYNC_POOL_SIZE = 2
    cfg.SB_ASYNC_WARM_START = True

    asyncio.run(send.async_bombing_mode(cfg))

    assert FakeSMTP.connect_calls == 2
    assert len(FakeSMTP.instances) == 2


def test_async_bombing_mode_cold_start_backoff(monkeypatch):
    import smtpburst.send.native as native

    asyncio.run(native.reset_async_pools())

    class FakeSMTP:
        connect_calls = 0
        attempts = 0

        def __init__(self, hostname, port, timeout=None, use_tls=False):
            self._connected = False

        async def connect(self):
            FakeSMTP.connect_calls += 1
            self._connected = True

        async def starttls(self):
            return None

        async def ehlo(self, host=None):
            return None

        async def sendmail(self, sender, receivers, message):
            FakeSMTP.attempts += 1
            if FakeSMTP.attempts == 1:
                raise RuntimeError("transient failure")

        async def quit(self):
            self._connected = False

        @property
        def is_connected(self):
            return self._connected

    async def immediate_throttle(*args, **kwargs):
        return None

    sleep_calls: list[float] = []

    async def record_sleep(delay, *_args):
        sleep_calls.append(delay)

    monkeypatch.setitem(sys.modules, "aiosmtplib", types.SimpleNamespace(SMTP=FakeSMTP))
    monkeypatch.setattr(native, "async_throttle", immediate_throttle)
    monkeypatch.setattr(native, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(native.random, "uniform", lambda a, b: 0.05)
    monkeypatch.setattr(native.asyncio, "sleep", record_sleep)

    cfg = Config()
    cfg.SB_SGEMAILS = 1
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    cfg.SB_ASYNC_POOL_SIZE = 1
    cfg.SB_ASYNC_COLD_START = True
    cfg.SB_RETRY_COUNT = 1

    asyncio.run(send.async_bombing_mode(cfg))

    assert sleep_calls == [pytest.approx(0.25)]
    assert FakeSMTP.connect_calls == 2
    assert FakeSMTP.attempts == 2
