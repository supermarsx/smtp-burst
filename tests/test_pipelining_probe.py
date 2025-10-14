from smtpburst.discovery import nettests


def test_pipelining_probe_success(monkeypatch):
    class DummySMTP:
        def __init__(self, *a, **k):
            self.esmtp_features = {"pipelining": ""}

        def ehlo(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    class DummySock:
        def __init__(self):
            self.stage = 0

        def settimeout(self, t):
            pass

        def recv(self, n):
            self.stage += 1
            if self.stage == 1:
                return b"220 banner\r\n"
            if self.stage == 2:
                return b"250-PIPELINING\r\n250 OK\r\n"
            return b"250 2.1.0 OK\r\n250 2.1.5 OK\r\n354 Start mail input\r\n"

        def sendall(self, data):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(nettests.smtplib, "SMTP", DummySMTP)
    monkeypatch.setattr(
        nettests.socket, "create_connection", lambda addr, timeout=5.0: DummySock()
    )
    res = nettests.pipelining_probe("h")
    assert res == {"advertised": True, "accepted": True}
