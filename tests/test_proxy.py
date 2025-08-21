import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import socket

import pytest

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


def test_invalid_order(tmp_path):
    path = tmp_path / "p.txt"
    path.write_text("a\nb\n")

    with pytest.raises(ValueError):
        proxy.load_proxies(str(path), order="bad")

    with pytest.raises(ValueError):
        proxy.select_proxy(["a", "b"], "bad", 0)


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

        def settimeout(self, t):
            calls["timeout"] = t

        def sendall(self, data):
            calls["send"] = True

        def recv(self, n):
            return b"HTTP/1.1 200 OK\r\n\r\n"

    def fake_create(addr, timeout=5):
        calls["conn"] = addr
        calls["create_timeout"] = timeout
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", fake_dns)
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    assert proxy.check_proxy("h:1", timeout=7)
    assert calls["ping"] == "h" and calls["dns"] == "h" and calls["conn"] == ("h", 1)
    assert calls["create_timeout"] == 7 and calls["timeout"] == 7


def test_check_proxy_failure(monkeypatch, caplog):
    monkeypatch.setattr(proxy, "ping", lambda h: "")
    with caplog.at_level(logging.WARNING):
        assert not proxy.check_proxy("bad:1")
        assert "Ping" in caplog.text


@pytest.mark.parametrize("msg", ["ping command not found", "ping command timed out"])
def test_check_proxy_ping_errors(monkeypatch, caplog, msg):
    monkeypatch.setattr(proxy, "ping", lambda h: msg)
    with caplog.at_level(logging.WARNING):
        assert not proxy.check_proxy("bad:1")
        assert "Ping" in caplog.text


def test_check_proxy_bad_status(monkeypatch):
    def fake_ping(host):
        return "pong"

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


def test_load_proxies_timeout(monkeypatch, tmp_path):
    path = tmp_path / "p.txt"
    path.write_text("a:1\n")
    called = {}

    def fake_check(p, timeout=None):
        called["timeout"] = timeout
        return True

    monkeypatch.setattr(proxy, "check_proxy", fake_check)
    proxy.load_proxies(str(path), check=True, timeout=9)
    assert called["timeout"] == 9


def test_check_proxy_timeout(monkeypatch, caplog):
    def fake_ping(host):
        return "pong"

    class DummySock:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def settimeout(self, t):
            pass

        def sendall(self, data):
            pass

        def recv(self, n):
            raise socket.timeout()

    def fake_create(addr, timeout=5):
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", lambda h: "1.2.3.4")
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    with caplog.at_level(logging.WARNING):
        assert not proxy.check_proxy("h:1")
        assert "timed out" in caplog.text
