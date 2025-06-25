import logging
from smtpburst import send
from smtpburst.config import Config


def test_login_test(monkeypatch, caplog):
    class DummySMTP:
        def __init__(self, host, port):
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
