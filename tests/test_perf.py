import smtpburst.attacks as attacks


def _monkey_time(monkeypatch, *values):
    it = iter(values)
    monkeypatch.setattr(attacks.time, "monotonic", lambda: next(it))


def test_connection_setup_time(monkeypatch):

    class DummySock:
        def close(self):
            pass

    monkeypatch.setattr(attacks.socket, "create_connection", lambda a: DummySock())
    _monkey_time(monkeypatch, 0.0, 0.5)
    assert attacks.connection_setup_time("h") == 0.5


def test_smtp_handshake_time(monkeypatch):

    class DummySMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def starttls(self):
            pass

        def ehlo(self):
            pass

    monkeypatch.setattr(attacks.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(attacks.smtplib, "SMTP_SSL", DummySMTP)
    _monkey_time(monkeypatch, 0.0, 0.4)
    assert attacks.smtp_handshake_time("h") == 0.4


def test_message_send_time(monkeypatch):

    class DummySMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def starttls(self):
            pass

        def sendmail(self, *a, **k):
            pass

    monkeypatch.setattr(attacks.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(attacks.smtplib, "SMTP_SSL", DummySMTP)
    _monkey_time(monkeypatch, 0.0, 0.7)
    assert (
        attacks.message_send_time("h", "s", ["r"], b"m")
        == 0.7
    )


def test_ping_latency(monkeypatch):
    monkeypatch.setattr(attacks.subprocess, "run", lambda *a, **k: None)
    _monkey_time(monkeypatch, 0.0, 0.2)
    assert attacks.ping_latency("h") == 0.2
