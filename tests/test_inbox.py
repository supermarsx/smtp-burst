import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import inbox
import imaplib
import poplib


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
    class DummyPOP:
        def __init__(self, host, port):
            assert host == "host"
            assert port == 995
            self.msgs = {1: b"abc", 2: b"def abc"}

        def user(self, u):
            assert u == "u"

        def pass_(self, p):
            assert p == "p"

        def list(self):
            return (b"+OK", [b"1 0", b"2 0"])

        def retr(self, i):
            return (b"+OK", [self.msgs[i]], len(self.msgs[i]))

        def quit(self):
            pass

    monkeypatch.setattr(inbox.poplib, "POP3_SSL", DummyPOP)
    ids = inbox.pop3_search("host", "u", "p", pattern=b"abc")
    assert ids == [1, 2]


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

        def list(self):
            raise AssertionError("should not be called")

        def retr(self, i):
            raise AssertionError("should not be called")

        def quit(self):
            closed["quit"] = True

    monkeypatch.setattr(inbox.poplib, "POP3_SSL", DummyPOP)
    ids = inbox.pop3_search("host", "u", "p", pattern=b"abc")
    assert ids == []
    assert closed["quit"]
