import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import inbox


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
