import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import logging
import socket

import pytest

from smtpburst import proxy
from smtpburst.discovery import nettests


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


def test_parse_proxy_auth():
    info = proxy.parse_proxy("user:pass@host:1080")
    assert info.host == "host" and info.port == 1080
    assert info.username == "user" and info.password == "pass"


def test_parse_proxy_ipv6():
    info = proxy.parse_proxy("[2001:db8::1]:8080")
    assert info.host == "2001:db8::1" and info.port == 8080
    info = proxy.parse_proxy("[2001:db8::1]")
    assert info.host == "2001:db8::1" and info.port == 1080


def test_parse_proxy_ipv6_unbracketed():
    info = proxy.parse_proxy("2001:db8::1:8080")
    assert info.host == "2001:db8::1" and info.port == 8080
    info = proxy.parse_proxy("2001:db8::1")
    assert info.host == "2001:db8::1" and info.port == 1080
    with pytest.raises(ValueError):
        proxy.parse_proxy("2001:db8::1:70000")


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

    res = proxy.check_proxy("h:1", timeout=7)
    assert isinstance(res, proxy.ProxyInfo)
    assert (
        res.host == "h"
        and res.port == 1
        and res.username is None
        and res.password is None
    )
    assert calls["ping"] == "h" and calls["dns"] == "h" and calls["conn"] == ("h", 1)
    assert calls["create_timeout"] == 7 and calls["timeout"] == 7


def test_check_proxy_auth(monkeypatch):
    calls = {}

    def fake_ping(host):
        calls["ping"] = host
        return "pong"

    def fake_dns(host):
        calls["dns"] = host
        return "1.2.3.4"

    class DummySock:
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

    res = proxy.check_proxy("user:pwd@h:1", timeout=7)
    assert isinstance(res, proxy.ProxyInfo)
    assert (
        res.host == "h"
        and res.port == 1
        and res.username == "user"
        and res.password == "pwd"
    )
    assert calls["ping"] == "h" and calls["dns"] == "h" and calls["conn"] == ("h", 1)
    assert calls["create_timeout"] == 7 and calls["timeout"] == 7


def test_check_proxy_failure(monkeypatch, caplog):
    monkeypatch.setattr(proxy, "ping", lambda h: "")
    with caplog.at_level(logging.WARNING):
        assert not proxy.check_proxy("bad:1")
        assert "Ping" in caplog.text


@pytest.mark.parametrize("case", ["missing", "timeout"])
def test_check_proxy_ping_errors(monkeypatch, caplog, case):
    if case == "missing":

        def fake_ping(host):
            raise nettests.CommandNotFoundError("ping")

    else:

        def fake_ping(host):
            return {"error": "timeout", "cmd": "ping"}

    monkeypatch.setattr(proxy, "ping", fake_ping)
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


def test_load_proxies_malformed_proxy_ignored(monkeypatch, tmp_path):
    path = tmp_path / "p.txt"
    path.write_text("good:1\nbad:abc\n")

    def fake_ping(host):
        return "pong"

    def fake_dns(host):
        return "1.2.3.4"

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
            return b"HTTP/1.1 200 OK\r\n\r\n"

    def fake_create(addr, timeout=5):
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", fake_dns)
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    proxies = proxy.load_proxies(str(path), check=True)
    assert proxies == ["good:1"]


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


def test_check_proxy_http_basic_auth(monkeypatch):
    sent = {}

    def fake_ping(host):
        return "pong"

    def fake_dns(host):
        return "1.2.3.4"

    class DummySock:
        data = b""

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def settimeout(self, t):
            pass

        def sendall(self, data):
            sent["data"] = data

        def recv(self, n):
            # Always accept
            return b"HTTP/1.1 200 Connection established\r\n\r\n"

    def fake_create(addr, timeout=5):
        return DummySock()

    monkeypatch.setattr(proxy, "ping", fake_ping)
    monkeypatch.setattr(proxy.socket, "gethostbyname", fake_dns)
    monkeypatch.setattr(proxy.socket, "create_connection", fake_create)

    info = proxy.check_proxy("user:pass@h:8080")
    assert info and sent["data"]
    assert b"Proxy-Authorization: Basic dXNlcjpwYXNz" in sent["data"]
