import logging
from smtpburst import send
from smtpburst.config import Config


def test_login_test(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"auth": "LOGIN PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            if self.user == "u" and self.password == "p":
                return (235, b"ok")
            raise send.smtplib.SMTPAuthenticationError(535, b"bad")

        def auth_login(self, challenge=None):
            return self.user if challenge is None else self.password

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERLIST = ["u"]
    cfg.SB_PASSLIST = ["p"]
    with caplog.at_level(logging.INFO, logger="smtpburst.send"):
        res = send.login_test(cfg)
    assert res == {"LOGIN": True, "PLAIN": True}
    assert any("Authentication LOGIN" in r.getMessage() for r in caplog.records)


def test_auth_test(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"auth": "LOGIN PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            if self.user == "u" and self.password == "p":
                return (235, b"ok")
            raise send.smtplib.SMTPAuthenticationError(535, b"bad")

        def auth_login(self, challenge=None):
            return self.user if challenge is None else self.password

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERNAME = "u"
    cfg.SB_PASSWORD = "p"
    with caplog.at_level(logging.INFO, logger="smtpburst.send"):
        res = send.auth_test(cfg)
    assert res == {"LOGIN": True, "PLAIN": True}
    assert any("Authentication LOGIN" in r.getMessage() for r in caplog.records)


def test_login_test_fail(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"auth": "LOGIN PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            if self.user == "u" and self.password == "p":
                return (235, b"ok")
            raise send.smtplib.SMTPAuthenticationError(535, b"bad")

        def auth_login(self, challenge=None):
            return self.user if challenge is None else self.password

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERLIST = ["wrong"]
    cfg.SB_PASSLIST = ["creds"]
    with caplog.at_level(logging.INFO, logger="smtpburst.send"):
        res = send.login_test(cfg)
    assert res == {"LOGIN": False, "PLAIN": False}
    assert any("Authentication LOGIN failed" in r.getMessage() for r in caplog.records)


def test_auth_test_fail(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"auth": "LOGIN PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            if self.user == "u" and self.password == "p":
                return (235, b"ok")
            raise send.smtplib.SMTPAuthenticationError(535, b"bad")

        def auth_login(self, challenge=None):
            return self.user if challenge is None else self.password

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERNAME = "wrong"
    cfg.SB_PASSWORD = "creds"
    with caplog.at_level(logging.INFO, logger="smtpburst.send"):
        res = send.auth_test(cfg)
    assert res == {"LOGIN": False, "PLAIN": False}
    assert any("Authentication LOGIN failed" in r.getMessage() for r in caplog.records)


def test_attempt_auth_passes_timeout(monkeypatch):
    timeouts = []

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            timeouts.append(timeout)
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            return (235, b"ok")

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    res = send._attempt_auth(
        "h",
        25,
        DummySMTP,
        "PLAIN",
        "u",
        "p",
        False,
        5.0,
    )
    assert res
    assert timeouts == [5.0]


def test_login_test_passes_timeout(monkeypatch):
    timeouts = []

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            timeouts.append(timeout)
            self.esmtp_features = {"auth": "PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            return (235, b"ok")

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERLIST = ["u"]
    cfg.SB_PASSLIST = ["p"]
    cfg.SB_TIMEOUT = 4.0
    res = send.login_test(cfg)
    assert res == {"PLAIN": True}
    assert timeouts == [4.0, 4.0]


def test_auth_test_passes_timeout(monkeypatch):
    timeouts = []

    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            timeouts.append(timeout)
            self.esmtp_features = {"auth": "PLAIN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            return (235, b"ok")

        def auth_plain(self, challenge=None):
            return f"\0{self.user}\0{self.password}"

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERNAME = "u"
    cfg.SB_PASSWORD = "p"
    cfg.SB_TIMEOUT = 3.0
    res = send.auth_test(cfg)
    assert res == {"PLAIN": True}
    assert timeouts == [3.0, 3.0]


def test_login_test_unknown_mechanism(monkeypatch):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"auth": "UNKNOWN"}
            self.user = None
            self.password = None

        def starttls(self):
            pass

        def ehlo(self):
            pass

        def auth(self, mech, authobj, initial_response_ok=True):
            return (235, b"ok")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(send.smtplib, "SMTP", DummySMTP)
    cfg = Config()
    cfg.SB_USERLIST = ["u"]
    cfg.SB_PASSLIST = ["p"]
    res = send.login_test(cfg)
    assert res == {"UNKNOWN": False}
