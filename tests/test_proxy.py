import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import proxy


def test_load_proxies_orders(tmp_path):
    path = tmp_path / "p.txt"
    path.write_text("a\nb\nc\n")
    assert proxy.load_proxies(str(path)) == ["a", "b", "c"]
    assert proxy.load_proxies(str(path), order="desc") == ["c", "b", "a"]
    res = proxy.load_proxies(str(path), order="random")
    assert sorted(res) == ["a", "b", "c"]


def test_select_proxy_orders():
    proxies = ["a", "b", "c"]
    assert proxy.select_proxy(proxies, "asc", 3) == "a"
    assert proxy.select_proxy(proxies, "desc", 1) == "b"
    p = proxy.select_proxy(proxies, "random", 5)
    assert p in proxies


def test_check_proxy(monkeypatch):
    calls = {}

    def fake_ping(host):
        calls["ping"] = host
        return "pong"

    def fake_dns(host):
        calls["dns"] = host
        return "1.2.3.4"

    class DummySock:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def sendall(self, data):
            calls["send"] = True

        def recv(self, n):
            return b"HTTP/1.1 200 OK\r\n\r\n"

    def fake_create(addr, timeout=5):
        calls["conn"] = addr
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", fake_dns)
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    assert proxy.check_proxy("h:1")
    assert calls["ping"] == "h" and calls["dns"] == "h" and calls["conn"] == ("h", 1)


def test_check_proxy_failure(monkeypatch):
    monkeypatch.setattr(proxy, "ping", lambda h: "")
    assert not proxy.check_proxy("bad:1")


def test_check_proxy_bad_status(monkeypatch):
    def fake_ping(host):
        return True

    class DummySock:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def sendall(self, data):
            pass

        def recv(self, n):
            return b"HTTP/1.1 403 Forbidden\r\n\r\n"

    def fake_create(addr, timeout=5):
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", lambda h: "1.2.3.4")
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    assert not proxy.check_proxy("h:1")
