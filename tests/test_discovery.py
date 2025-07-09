import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import discovery
from smtpburst.discovery import nettests


class DummyAns:
    def __init__(self, text):
        self._text = text

    def to_text(self):
        return self._text


def test_check_dmarc(monkeypatch):
    def fake_resolve(domain, record):
        assert domain == "_dmarc.example.com"
        assert record == "TXT"
        return [DummyAns("v=DMARC1; p=none")]

    monkeypatch.setattr(discovery.resolver, "resolve", fake_resolve)
    assert discovery.check_dmarc("example.com") == ["v=DMARC1; p=none"]


def test_check_spf(monkeypatch):
    def fake_resolve(domain, record):
        return [DummyAns("v=spf1 include:foo"), DummyAns("hello")]

    monkeypatch.setattr(discovery.resolver, "resolve", fake_resolve)
    assert discovery.check_spf("ex.com") == ["v=spf1 include:foo"]


def test_ping_posix(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["ping", "-c", "1", "host"]
        return SimpleNamespace(stdout="pong", returncode=0)

    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")
    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.ping("host") == "pong"


def test_ping_windows(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["ping", "-n", "1", "host"]
        return SimpleNamespace(stdout="pong", returncode=0)

    monkeypatch.setattr(nettests.platform, "system", lambda: "Windows")
    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.ping("host") == "pong"


def test_ping_failure(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["ping", "-c", "1", "host"]
        return SimpleNamespace(stdout="error", returncode=1)

    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")
    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.ping("host") == ""


def test_traceroute_posix(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["traceroute", "host"]
        return SimpleNamespace(stdout="trace")

    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")
    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.traceroute("host") == "trace"


def test_traceroute_windows(monkeypatch):
    def fake_run(cmd, capture_output, text, check):
        assert cmd == ["tracert", "host"]
        return SimpleNamespace(stdout="trace")

    monkeypatch.setattr(nettests.platform, "system", lambda: "Windows")
    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.traceroute("host") == "trace"


def test_check_rbl(monkeypatch):
    calls = []

    def fake_resolve(domain, record):
        calls.append(domain)
        if "listed" in domain:
            return [DummyAns("127.0.0.2")]
        raise discovery.resolver.NXDOMAIN

    monkeypatch.setattr(nettests.resolver, "resolve", fake_resolve)
    res = nettests.blacklist_check("1.2.3.4", ["listed.example", "clean.example"])
    assert res == {"listed.example": "listed", "clean.example": "not listed"}
    assert calls == ["4.3.2.1.listed.example", "4.3.2.1.clean.example"]


def test_check_rbl_ipv6(monkeypatch):
    calls = []

    def fake_resolve(domain, record):
        calls.append(domain)
        raise discovery.resolver.NXDOMAIN

    monkeypatch.setattr(nettests.resolver, "resolve", fake_resolve)
    res = nettests.blacklist_check("2001:db8::1", ["zone.example"])
    expected = (
        "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.8.b.d.0.1.0.0.2"
        ".zone.example"
    )
    assert res == {"zone.example": "not listed"}
    assert calls == [expected]


def test_open_relay_test(monkeypatch):
    class DummySMTP:
        def __init__(self, *args, **kwargs):
            pass

        def helo(self, _):
            return (250, b"ok")

        def mail(self, _):
            return (250, b"ok")

        def rcpt(self, _):
            return (250, b"ok")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(nettests.smtplib, "SMTP", DummySMTP)
    assert nettests.open_relay_test("host")


def test_lookup_mx(monkeypatch):
    def fake_resolve(domain, record):
        assert record == "MX"
        return [
            SimpleNamespace(
                preference=10,
                exchange=SimpleNamespace(to_text=lambda: "mail.example.com"),
            )
        ]

    monkeypatch.setattr(discovery.resolver, "resolve", fake_resolve)
    assert discovery.lookup_mx("ex.com") == ["10 mail.example.com"]


def test_smtp_extensions(monkeypatch):
    class DummySMTP:
        def __init__(self, *a, **k):
            self.esmtp_features = {"size": "", "starttls": ""}

        def ehlo(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(discovery.smtplib, "SMTP", DummySMTP)
    assert discovery.smtp_extensions("h") == ["size", "starttls"]


def test_check_certificate(monkeypatch):
    class DummyRaw:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    class DummySock(DummyRaw):
        def getpeercert(self):
            return {"subject": "s", "issuer": "i", "notBefore": "b", "notAfter": "a"}

    class DummyCtx:
        def wrap_socket(self, sock, server_hostname=None):
            return DummySock()

    monkeypatch.setattr(
        discovery.ssl,
        "create_default_context",
        lambda: DummyCtx(),
    )
    monkeypatch.setattr(
        discovery.socket,
        "create_connection",
        lambda addr, timeout=3: DummyRaw(),
    )

    res = discovery.check_certificate("h")
    assert res["subject"] == "s"
    assert res["issuer"] == "i"


def test_port_scan(monkeypatch):
    class DummySocket:
        def __init__(self):
            self.connected = []

        def settimeout(self, t):
            pass

        def connect(self, addr):
            if addr[1] == 25:
                return
            raise OSError

        def close(self):
            pass

    monkeypatch.setattr(discovery.socket, "socket", DummySocket)
    res = discovery.port_scan("h", [25, 26])
    assert res == {25: True, 26: False}


def test_probe_honeypot(monkeypatch):
    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def recv(self, n):
            return b"HoneySMTP ready"

    monkeypatch.setattr(
        discovery.socket, "create_connection", lambda addr, timeout=3: DummyConn()
    )
    assert discovery.probe_honeypot("h")


def test_vrfy_enum(monkeypatch):
    class DummySMTP:
        def __init__(self, *a, **k):
            pass

        def helo(self, _):
            pass

        def verify(self, u):
            return (250, b"ok") if u == "good" else (550, b"bad")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(nettests.smtplib, "SMTP", DummySMTP)
    res = nettests.vrfy_enum("h", ["good", "bad"])
    assert res == {"good": True, "bad": False}


def test_expn_enum(monkeypatch):
    class DummySMTP:
        def __init__(self, *a, **k):
            pass

        def helo(self, _):
            pass

        def expn(self, u):
            return (250, b"ok") if u == "list" else (550, b"bad")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(nettests.smtplib, "SMTP", DummySMTP)
    res = nettests.expn_enum("h", ["list", "none"])
    assert res == {"list": True, "none": False}


def test_rcpt_enum(monkeypatch):
    class DummySMTP:
        def __init__(self, *a, **k):
            pass

        def helo(self, _):
            pass

        def mail(self, _):
            return (250, b"ok")

        def rcpt(self, r):
            return (250, b"ok") if r == "ok" else (550, b"bad")

        def rset(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    monkeypatch.setattr(nettests.smtplib, "SMTP", DummySMTP)
    res = nettests.rcpt_enum("h", ["ok", "bad"])
    assert res == {"ok": True, "bad": False}
