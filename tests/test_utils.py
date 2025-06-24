import os
import sys
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst.send import sizeof_fmt, sendmail
from smtpburst import send as burstGen
from smtpburst import config as burstVars
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

    fail_counter = DummyCounter(burstVars.SB_STOPFQNT)

    smtp_mock = MagicMock()
    monkeypatch.setattr(burstGen.smtplib, "SMTP", smtp_mock)

    sendmail(1, 1, fail_counter, b"msg")

    assert not smtp_mock.called


def test_parse_server_default_port():
    host, port = burstGen.parse_server("example.com")
    assert host == "example.com"
    assert port == 25


def test_parse_server_with_port():
    host, port = burstGen.parse_server("example.com:2525")
    assert host == "example.com"
    assert port == 2525


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
