import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import inbox
import imaplib


def test_imap_search(monkeypatch):
    class DummyIMAP:
        def __init__(self, host, port):
            assert host == "host"
            assert port == 993

        def login(self, user, pwd):
            assert user == "u"
            assert pwd == "p"

        def select(self, mbox):
            assert mbox == "INBOX"

        def search(self, charset, criteria):
            assert charset is None
            assert criteria == "ALL"
            return ("OK", [b"1 2"])

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(inbox.imaplib, "IMAP4_SSL", DummyIMAP)
    ids = inbox.imap_search("host", "u", "p")
    assert ids == [b"1", b"2"]


def test_pop3_search(monkeypatch):
    called = {"stat": False, "retr": 0}
    msg_count = 1000

    class DummyPOP:
        def __init__(self, host, port):
            assert host == "host"
            assert port == 995
            self.msgs = {1: b"abc", 2: b"def abc"}

        def user(self, u):
            assert u == "u"

        def pass_(self, p):
            assert p == "p"

        def stat(self):
            called["stat"] = True
            return (msg_count, 0)

        def retr(self, i):
            called["retr"] += 1
            msg = self.msgs.get(i, b"ghi")
            return (b"+OK", [msg], len(msg))

        def quit(self):
            pass

    monkeypatch.setattr(inbox.poplib, "POP3_SSL", DummyPOP)
    ids = inbox.pop3_search("host", "u", "p", pattern=b"abc")
    assert ids == [1, 2]
    assert called["stat"]
    assert called["retr"] == msg_count


def test_imap_search_error(monkeypatch):
    closed = {"closed": False}

    class DummyIMAP:
        def __init__(self, host, port):
            pass

        def login(self, user, pwd):
            raise imaplib.IMAP4.error("auth failed")

        def select(self, mbox):
            raise AssertionError("should not be called")

        def search(self, charset, criteria):
            raise AssertionError("should not be called")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            closed["closed"] = True

    monkeypatch.setattr(inbox.imaplib, "IMAP4_SSL", DummyIMAP)
    ids = inbox.imap_search("host", "u", "p")
    assert ids == []
    assert closed["closed"]


def test_pop3_search_error(monkeypatch):
    closed = {"quit": False}

    class DummyPOP:
        def __init__(self, host, port):
            pass

        def user(self, u):
            raise OSError("network")

        def pass_(self, p):
            raise AssertionError("should not be called")

        def stat(self):
            raise AssertionError("should not be called")

        def retr(self, i):
            raise AssertionError("should not be called")

        def quit(self):
            closed["quit"] = True

    monkeypatch.setattr(inbox.poplib, "POP3_SSL", DummyPOP)
    ids = inbox.pop3_search("host", "u", "p", pattern=b"abc")
    assert ids == []
    assert closed["quit"]


def test_imap_header_search(monkeypatch):
    class DummyIMAP:
        def __init__(self, host, port):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def login(self, user, password):
            pass

        def select(self, mailbox):
            pass

        def search(self, charset, *criteria):
            assert criteria == ("HEADER", "X-Trace", "trace-123")
            return ("OK", [b"1 2"])

    monkeypatch.setattr(inbox.imaplib, "IMAP4_SSL", DummyIMAP)
    res = inbox.imap_header_search("h", "u", "p", "X-Trace", "trace-123")
    assert res == [b"1", b"2"]
