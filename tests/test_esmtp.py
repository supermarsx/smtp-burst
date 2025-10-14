from smtpburst.discovery import esmtp


def test_esmtp_check_features_and_8bit(monkeypatch):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {"SIZE": "", "8BITMIME": "", "PIPELINING": ""}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self):
            pass

        def sendmail(self, sender, rcpts, body):
            # allow 8-bit body because 8BITMIME is advertised
            return {}

    monkeypatch.setattr(esmtp.smtplib, "SMTP", DummySMTP)

    res = esmtp.check("h")
    assert set(res["features"]) >= {"size", "8bitmime", "pipelining"}
    assert res["supports"]["8bitmime"] is True
    assert res["tests"]["eight_bit_send"] is True


def test_esmtp_check_8bit_fail(monkeypatch):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            self.esmtp_features = {}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self):
            pass

        def sendmail(self, sender, rcpts, body):
            # Reject 8-bit when 8BITMIME not present
            if any(b > 127 for b in body):
                raise esmtp.smtplib.SMTPDataError(554, b"8-bit not allowed")
            return {}

    monkeypatch.setattr(esmtp.smtplib, "SMTP", DummySMTP)

    res = esmtp.check("h")
    assert res["supports"]["8bitmime"] is False
    assert res["tests"]["eight_bit_send"] is False


def test_esmtp_smtputf8_and_size_enforced(monkeypatch):
    class DummySMTP:
        def __init__(self, host, port, timeout=None):
            # SIZE=10 keeps test message tiny
            self.esmtp_features = {"SMTPUTF8": "", "SIZE": "10"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def ehlo(self):
            pass

        def sendmail(self, sender, rcpts, body, mail_options=(), rcpt_options=()):
            if "SMTPUTF8" in mail_options:
                ok_utf8 = True
            else:
                ok_utf8 = False
            if len(body) > 10:
                raise esmtp.smtplib.SMTPDataError(552, b"too big")
            if not ok_utf8:
                raise esmtp.smtplib.SMTPDataError(550, b"missing SMTPUTF8")
            return {}

    monkeypatch.setattr(esmtp.smtplib, "SMTP", DummySMTP)

    res = esmtp.check("h")
    assert res["supports"]["smtputf8"] is True
    assert res["tests"]["smtp_utf8_send"] is True
    assert res["tests"]["size_enforced"] is True
