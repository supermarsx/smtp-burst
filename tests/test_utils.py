import os
import sys
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
    host, port = burstGen.parse_server("example.com:bad")
    assert host == "example.com"
    assert port == 25


def test_open_sockets_creates_connections(monkeypatch):
    connections = []

    class DummySocket:
        def close(self):
            pass

    def fake_create_connection(addr):
        connections.append(addr)
        return DummySocket()

    def fake_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(burstGen.socket, "create_connection", fake_create_connection)
    monkeypatch.setattr(burstGen.time, "sleep", fake_sleep)

    burstGen.open_sockets("host", 3, port=123)

    assert connections == [("host", 123)] * 3


def test_open_sockets_continues_on_errors(monkeypatch, caplog):
    attempts = []

    class DummySocket:
        def close(self):
            pass

    def fake_create_connection(addr):
        attempts.append(addr)
        if len(attempts) == 1:
            raise OSError("boom")
        return DummySocket()

    def fake_sleep(_):
        raise KeyboardInterrupt

    monkeypatch.setattr(burstGen.socket, "create_connection", fake_create_connection)
    monkeypatch.setattr(burstGen.time, "sleep", fake_sleep)

    with caplog.at_level(logging.WARNING, logger="smtpburst.attacks"):
        burstGen.open_sockets("host", 3, port=123)

    assert attempts == [("host", 123)] * 3
    assert any("Failed to open socket" in r.getMessage() for r in caplog.records)


def test_open_sockets_duration(monkeypatch):
    closed = []

    class DummySocket:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(burstGen.socket, "create_connection", lambda a: DummySocket())

    vals = iter([0, 0, 1, 2])

    def fake_monotonic():
        return next(vals)

    sleep_calls = []

    monkeypatch.setattr(burstGen.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(burstGen.time, "sleep", lambda x: sleep_calls.append(x))

    burstGen.open_sockets("host", 2, port=25, duration=2)

    assert len(closed) == 2
    assert len(sleep_calls) == 2


def test_open_sockets_iterations(monkeypatch):
    closed = []

    class DummySocket:
        def close(self):
            closed.append(True)

    monkeypatch.setattr(burstGen.socket, "create_connection", lambda a: DummySocket())
    sleep_calls = []
    monkeypatch.setattr(burstGen.time, "sleep", lambda x: sleep_calls.append(x))

    burstGen.open_sockets("host", 1, port=25, iterations=3)

    assert len(closed) == 1
    assert len(sleep_calls) == 3


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

    class DummySMTP:
        def __init__(self, *args, **kwargs):
            calls["smtp"] = True

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
            captured['timeout'] = kwargs.get('timeout')

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    cfg.SB_TIMEOUT = 7.5
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg)
    assert captured['timeout'] == pytest.approx(7.5)


def test_sendmail_passes_timeout_ssl(monkeypatch):
    captured = {}

    class DummySSL:
        def __init__(self, *args, **kwargs):
            captured['timeout'] = kwargs.get('timeout')

        def sendmail(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(burstGen.smtplib, "SMTP_SSL", DummySSL)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    cfg.SB_TIMEOUT = 6.0
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg, use_ssl=True)
    assert captured['timeout'] == pytest.approx(6.0)


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

    monkeypatch.setattr(burstGen.smtplib, "SMTP", DummySMTP)

    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    cfg = Config()
    counter = DummyCounter()
    sendmail(1, 1, counter, b"msg", cfg, start_tls=True)
    assert called.get("starttls")


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
