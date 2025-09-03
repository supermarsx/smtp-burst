import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import discovery


def test_banner_check_success(monkeypatch):
    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def recv(self, n):
            return b"220 test banner"

    calls = {}

    def fake_create(addr, timeout=5):
        calls["addr"] = addr
        return DummyConn()

    monkeypatch.setattr(discovery.socket, "create_connection", fake_create)
    monkeypatch.setattr(discovery.send, "parse_server", lambda s: ("host", 2525))
    monkeypatch.setattr(discovery.rdns, "verify", lambda h: True)

    banner, ok = discovery.banner_check("host:2525")
    assert banner == "220 test banner"
    assert ok
    assert calls["addr"] == ("host", 2525)


def test_banner_check_rdns_fail(monkeypatch):
    class DummyConn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def recv(self, n):
            return b"220 test"

    monkeypatch.setattr(
        discovery.socket,
        "create_connection",
        lambda addr, timeout=5: DummyConn(),
    )
    monkeypatch.setattr(discovery.send, "parse_server", lambda s: ("host", 25))
    monkeypatch.setattr(discovery.rdns, "verify", lambda h: False)

    banner, ok = discovery.banner_check("host")
    assert banner == "220 test"
    assert not ok


from smtpburst import __main__ as main_mod


def test_main_banner_check_report(monkeypatch):
    called = {}

    def fake_banner_check(server):
        called["server"] = server
        return ("banner", True)

    def fake_report(res):
        called["report"] = res
        return "formatted"

    monkeypatch.setattr(main_mod.discovery, "banner_check", fake_banner_check)
    monkeypatch.setattr(main_mod, "ascii_report", fake_report)
    monkeypatch.setattr(main_mod.send, "bombing_mode", lambda cfg, attachments=None: None)

    main_mod.main(["--banner-check", "--server", "srv"])

    assert called["server"] == "srv"
    assert called["report"] == {"banner": "banner", "reverse_dns": "PASS"}
