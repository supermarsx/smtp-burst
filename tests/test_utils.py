import pytest
import logging

# Ensure the project root is on sys.path

from smtpburst.send import sizeof_fmt, sendmail, throttle
from smtpburst import send as burstGen
from smtpburst import datagen
from smtpburst.config import Config
from unittest.mock import MagicMock


def test_sizeof_fmt_1kib():
    assert sizeof_fmt(1024) == "1.0KiB"


def test_sizeof_fmt_1_5kib():
    assert sizeof_fmt(1536) == "1.5KiB"


def test_sendmail_exits_when_failcount_exceeded(monkeypatch):
    """sendmail should not create an SMTP object once failure threshold hit."""

    class DummyCounter:
        def __init__(self, value):
            self.value = value

    cfg = Config()
    fail_counter = DummyCounter(cfg.SB_STOPFQNT)

    smtp_mock = MagicMock()
    monkeypatch.setattr(burstGen.smtplib, "SMTP", smtp_mock)

    sendmail(1, 1, fail_counter, b"msg", cfg)

    assert not smtp_mock.called


def test_parse_server_default_port():
    host, port = burstGen.parse_server("example.com")
    assert host == "example.com"
    assert port == 25


def test_parse_server_with_port():
    host, port = burstGen.parse_server("example.com:2525")
    assert host == "example.com"
    assert port == 2525


def test_parse_server_bad_port():
    with pytest.raises(ValueError):
        burstGen.parse_server("example.com:bad")


def test_parse_server_ipv6_with_port():
    host, port = burstGen.parse_server("[2001:db8::1]:587")
    assert host == "2001:db8::1"
    assert port == 587


def test_parse_server_ipv6_default_port():
    host, port = burstGen.parse_server("[2001:db8::1]")
    assert host == "2001:db8::1"
    assert port == 25


def test_parse_server_bare_ipv6():
    host, port = burstGen.parse_server("2001:db8::1")
    assert host == "2001:db8::1"
    assert port == 25


def test_open_sockets_creates_connections(monkeypatch):
    connections = []

    class DummySocket:
        def close(self):
            pass

    def fake_create_connection(addr, timeout=None):
        connections.append(addr)
        return DummySocket()

    def fake_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        burstGen.attacks.socket, "create_connection", fake_create_connection
    )
    monkeypatch.setattr(burstGen.attacks.time, "sleep", fake_sleep)

    burstGen.open_sockets("host", 3, port=123)

    assert connections == [("host", 123)] * 3


def test_open_sockets_continues_on_errors(monkeypatch, caplog):
    attempts = []

    class DummySocket:
        def close(self):
            pass

    def fake_create_connection(addr, timeout=None):
        attempts.append(addr)
        if len(attempts) == 1:
            raise OSError("boom")
        return DummySocket()

    def fake_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(
        burstGen.attacks.socket, "create_connection", fake_create_connection
    )
    monkeypatch.setattr(burstGen.attacks.time, "sleep", fake_sleep)

    with caplog.at_level(logging.WARNING, logger="smtpburst.attacks"):
        burstGen.open_sockets("host", 3, port=123)

    assert attempts == [("host", 123)] * 3
    assert any("Failed to open socket" in r.getMessage() for r in caplog.records)


def test_open_sockets_duration(monkeypatch):
    closed = []

    class DummySocket:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(
        burstGen.attacks.socket,
        "create_connection",
        lambda a, timeout=None: DummySocket(),
    )

    vals = iter([0, 0, 1, 2])

    def fake_monotonic():
        return next(vals)

    sleep_calls = []

    monkeypatch.setattr(burstGen.attacks.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(burstGen.attacks.time, "sleep", lambda x: sleep_calls.append(x))

    burstGen.open_sockets("host", 2, port=25, duration=2)

    assert len(closed) == 2
    assert len(sleep_calls) == 2


def test_open_sockets_iterations(monkeypatch):
    closed = []

    class DummySocket:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(
        burstGen.attacks.socket,
        "create_connection",
        lambda a, timeout=None: DummySocket(),
    )
    sleep_calls = []
    monkeypatch.setattr(burstGen.attacks.time, "sleep", lambda x: sleep_calls.append(x))

    burstGen.open_sockets("host", 1, port=25, iterations=3)

    assert len(closed) == 1
    assert len(sleep_calls) == 3


def test_attacks_open_sockets_uses_timeout(monkeypatch):
    captured = []

    class DummySocket:
        def close(self):
            pass

    def fake_create_connection(addr, timeout=None):
        captured.append(timeout)
        return DummySocket()

    monkeypatch.setattr(
        burstGen.attacks.socket, "create_connection", fake_create_connection
    )
    monkeypatch.setattr(
        burstGen.attacks.time,
        "sleep",
        lambda x: (_ for _ in ()).throw(KeyboardInterrupt),
    )

    burstGen.attacks.open_sockets("h", 1, port=25, timeout=5.5)

    assert captured == [pytest.approx(5.5)]


def test_send_open_sockets_forwards_timeout(monkeypatch):
    called = {}

    def fake_open(
        host, count, port, delay, cfg, *, duration=None, iterations=None, timeout=None
    ):
        called["timeout"] = timeout

    monkeypatch.setattr(burstGen.attacks, "open_sockets", fake_open)

    cfg = Config()
    cfg.SB_TIMEOUT = 8.2
    burstGen.open_sockets("host", 1, port=25, cfg=cfg)

    assert called["timeout"] == pytest.approx(8.2)


def test_sendmail_reports_auth_success(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def login(self, user, pwd):
            if user == "u" and pwd == "p":
                return
            raise burstGen.SMTPException

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    counter = DummyCounter()
    with caplog.at_level(logging.INFO, logger="smtpburst.send"):
        sendmail(1, 1, counter, b"msg", cfg, server="s", users=["u"], passwords=["p"])
    assert any("Auth success: u:p" in r.getMessage() for r in caplog.records)


def test_sendmail_uses_ssl(monkeypatch):
    calls = {}

    class DummySSL:
        def __init__(self, *args, **kwargs):
            calls["ssl"] = True

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            calls["smtp"] = True

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySSL)
    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg, use_ssl=True)
    assert calls.get("ssl") and not calls.get("smtp")


def test_sendmail_passes_timeout(monkeypatch):
    captured = {}

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    cfg.SB_TIMEOUT = 7.5
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg)
    assert captured["timeout"] == pytest.approx(7.5)


def test_sendmail_passes_timeout_ssl(monkeypatch):
    captured = {}

    class DummySSL:
        def __init__(self, *args, **kwargs):
            captured["timeout"] = kwargs.get("timeout")

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySSL)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    cfg.SB_TIMEOUT = 6.0
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg, use_ssl=True)
    assert captured["timeout"] == pytest.approx(6.0)


def test_sendmail_calls_starttls(monkeypatch):
    called = {}

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def starttls(self):
            called["starttls"] = True

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg, start_tls=True)
    assert called.get("starttls")


def test_sendmail_uses_proxy_socket(monkeypatch):
    import types
    import sys

    class DummySock:
        created = False
        proxy = None
        connected = None

        def __init__(self, *a, **k):
            DummySock.created = True

        def set_proxy(self, typ, host, port):
            DummySock.proxy = (typ, host, port)

        def settimeout(self, timeout):
            pass

        def bind(self, addr):
            pass

        def connect(self, addr):
            DummySock.connected = addr

    dummy_socks = types.SimpleNamespace(socksocket=DummySock, SOCKS5=1)
    monkeypatch.setitem(sys.modules, "socks", dummy_socks)

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            self.debuglevel = 0
            self.source_address = None
            self._get_socket(args[0], args[1], kwargs.get("timeout"))

        def starttls(self):
            pass

        def sendmail(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def _get_socket(self, host, port, timeout):  # pragma: no cover - replaced
            return object()

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySMTP)

    orig_socket = burstGen.socket.socket

    class Counter:
        value = 0

    cfg = Config()
    sendmail(1, 1, Counter(), b"m", cfg, server="h:25", proxy="p:1080")

    assert burstGen.socket.socket is orig_socket
    assert DummySock.created
    assert DummySock.proxy == (1, "p", 1080)
    assert DummySock.connected == ("h", 25)


def test_sendmail_proxy_missing_pysocks(monkeypatch, caplog):
    import builtins

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "socks":
            raise ImportError
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def sendmail(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySMTP)

    class Counter:
        value = 0

    cfg = Config()
    with caplog.at_level(logging.WARNING, logger="smtpburst.send"):
        sendmail(1, 1, Counter(), b"m", cfg, server="h:25", proxy="p:1080")

    assert any("PySocks" in r.getMessage() for r in caplog.records)


def test_sendmail_proxy_warning(monkeypatch, caplog):
    """Using a proxy without PySocks should log a warning."""
    import builtins

    orig_import = builtins.__import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "socks":
            raise ImportError
        return orig_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def sendmail(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self, host=None):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySMTP)

    class Counter:
        value = 0

    cfg = Config()
    with caplog.at_level(logging.WARNING, logger="smtpburst.send"):
        sendmail(1, 1, Counter(), b"m", cfg, server="h:25", proxy="p:1080")

    msgs = [r.getMessage() for r in caplog.records]
    assert any("PySocks" in m and "ignoring" in m for m in msgs)


def test_append_message_uses_subject_and_body(monkeypatch):
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_BODY = "Body"
    cfg.SB_SIZE = 0
    msg = burstGen.append_message(cfg)
    assert b"Subject: Sub" in msg
    assert b"Body" in msg


def test_append_message_html_body():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_BODY = "Body"
    cfg.SB_HTML_BODY = "<p>HTML</p>"
    cfg.SB_SIZE = 0
    msg_bytes = burstGen.append_message(cfg)
    import email

    msg = email.message_from_bytes(msg_bytes)
    assert msg.is_multipart()
    # first part is plain text with body, second part is html
    parts = msg.get_payload()
    assert len(parts) == 2
    assert parts[1].get_content_type() == "text/html"
    assert "<p>HTML</p>" in parts[1].get_payload()


def test_append_message_template():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_TEMPLATE = "Hello {receiver} from {sender}"
    cfg.SB_SIZE = 0
    msg = burstGen.append_message(cfg)
    assert b"Hello c@d.com" in msg


def test_append_message_unicode_headers():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_SIZE = 0
    cfg.SB_TEST_UNICODE = True
    msg = burstGen.append_message(cfg)
    assert b"FrOm:" in msg and b"tO:" in msg


def test_append_message_utf7_body():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_BODY = "\u2713"  # checkmark
    cfg.SB_SIZE = 0
    cfg.SB_TEST_UTF7 = True
    msg = burstGen.append_message(cfg)
    assert b"+JxM" in msg


def test_append_message_tunnel_header():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_SIZE = 0
    cfg.SB_TEST_TUNNEL = True
    msg = burstGen.append_message(cfg)
    assert b"X-Orig: overlap" in msg


def test_append_message_control_chars():
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_SIZE = 0
    cfg.SB_TEST_CONTROL = True
    msg = burstGen.append_message(cfg)
    assert b"\x01\x02" in msg


def test_append_message_with_attachment(tmp_path):
    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com"]
    cfg.SB_SUBJECT = "Sub"
    cfg.SB_SIZE = 0
    att = tmp_path / "f.txt"
    att.write_text("hello")
    msg_bytes = burstGen.append_message(cfg, [str(att)])
    import email

    m = email.message_from_bytes(msg_bytes)
    assert m.is_multipart()
    payload = m.get_payload()
    assert len(payload) == 2
    assert payload[1].get_filename() == "f.txt"
    assert payload[1].get_payload(decode=True) == b"hello"


def test_genData_length():
    for n in [0, 1, 10, 100]:
        assert len(datagen.generate(n, mode=datagen.DataMode.ASCII)) == n


def test_throttle_combines_delay(monkeypatch):
    calls = []

    def fake_sleep(val):
        calls.append(val)

    monkeypatch.setattr(burstGen.time, "sleep", fake_sleep)
    cfg = Config()
    cfg.SB_GLOBAL_DELAY = 0.5
    throttle(cfg, 0.2)
    assert calls and calls[0] == pytest.approx(0.7)
