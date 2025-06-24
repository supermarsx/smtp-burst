import os
import sys
import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from burstGen import sizeof_fmt
from burstGen import sendmail
import burstGen
import burstVars
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


def test_sendmail_retries_with_proxies(monkeypatch):
    class DummyCounter:
        def __init__(self, value=0):
            self.value = value

    burstVars.SB_PROXIES = ["p1", "p2"]
    burstVars.SB_ROTATE_PROXIES = True
    burstGen.SB_PROXIES = burstVars.SB_PROXIES
    burstGen.SB_ROTATE_PROXIES = burstVars.SB_ROTATE_PROXIES
    counter = DummyCounter()
    calls = []

    def open_mock(server, proxy=None):
        class Ctx:
            def __enter__(self_inner):
                calls.append(proxy)
                if proxy == "p1":
                    raise OSError("fail")
                return MagicMock()

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        return Ctx()

    monkeypatch.setattr(burstGen, "open_smtp", open_mock)

    sendmail(1, 1, counter, b"msg")

    assert calls == ["p1", "p2"]
    burstVars.SB_PROXIES = []
    burstVars.SB_ROTATE_PROXIES = False
    burstGen.SB_PROXIES = []
    burstGen.SB_ROTATE_PROXIES = False
