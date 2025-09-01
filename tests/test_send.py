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


@pytest.mark.asyncio
async def test_async_bombing_mode(monkeypatch):
    """Async mode should send expected emails without spawning processes."""

    sent = []

    def fake_sendmail(number, burst, counter, msg, cfg, **kwargs):
        sent.append((number, burst, msg))

    monkeypatch.setattr(send, "sendmail", fake_sendmail)
    monkeypatch.setattr(send, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))

    import multiprocessing

    def boom(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("Process should not be spawned in async mode")

    monkeypatch.setattr(multiprocessing, "Process", boom)

    cfg = Config()
    cfg.SB_SGEMAILS = 2
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    await send.async_bombing_mode(cfg)

    assert len(sent) == 2
    for number, burst, msg in sent:
        assert number in {1, 2}
        assert burst == 1
        assert msg == b"msg"
