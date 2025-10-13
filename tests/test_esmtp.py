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
