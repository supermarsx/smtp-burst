import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst import discovery


class DummyAns:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


def test_check_dmarc(monkeypatch):
    def fake_resolve(domain, record):
        assert domain == '_dmarc.example.com'
        assert record == 'TXT'
        return [DummyAns('v=DMARC1; p=none')]

    monkeypatch.setattr(discovery.resolver, 'resolve', fake_resolve)
    assert discovery.check_dmarc('example.com') == ['v=DMARC1; p=none']


def test_check_spf(monkeypatch):
    def fake_resolve(domain, record):
        return [DummyAns('v=spf1 include:foo'), DummyAns('hello')]

    monkeypatch.setattr(discovery.resolver, 'resolve', fake_resolve)
    assert discovery.check_spf('ex.com') == ['v=spf1 include:foo']


def test_ping(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd[-1] == 'host'
        return SimpleNamespace(stdout='pong')

    monkeypatch.setattr(discovery.subprocess, 'run', fake_run)
    assert discovery.ping('host') == 'pong'


def test_traceroute(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd[-1] == 'host'
        return SimpleNamespace(stdout='trace')

    monkeypatch.setattr(discovery.subprocess, 'run', fake_run)
    assert discovery.traceroute('host') == 'trace'
