import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst.discovery import rdns


def test_verify_rdns_success(monkeypatch):
    def fake_gethostbyname(host):
        return "1.2.3.4"

    def fake_gethostbyaddr(ip):
        assert ip == "1.2.3.4"
        return ("mail.example.com", [], [ip])

    monkeypatch.setattr(rdns.socket, "gethostbyname", fake_gethostbyname)
    monkeypatch.setattr(rdns.socket, "gethostbyaddr", fake_gethostbyaddr)

    assert rdns.verify("example.com")


def test_verify_rdns_failure(monkeypatch):
    def fake_gethostbyname(host):
        if host == "example.com":
            return "1.2.3.4"
        return "5.6.7.8"

    def fake_gethostbyaddr(ip):
        return ("other.example.com", [], [ip])

    monkeypatch.setattr(rdns.socket, "gethostbyname", fake_gethostbyname)
    monkeypatch.setattr(rdns.socket, "gethostbyaddr", fake_gethostbyaddr)

    assert not rdns.verify("example.com")
