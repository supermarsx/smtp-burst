from types import SimpleNamespace
from smtpburst.discovery import mta


def test_mta_sts_policy(monkeypatch):
    def fake_resolve(qname, rtype):
        assert qname == "_mta-sts.example.com" and rtype == "TXT"
        return [SimpleNamespace(to_text=lambda: "v=STSv1; id=20251001T")]

    monkeypatch.setattr(mta.resolver, "resolve", fake_resolve)
    res = mta.mta_sts_policy("example.com")
    assert res == ["v=STSv1; id=20251001T"]


def test_dane_tlsa(monkeypatch):
    def fake_resolve(qname, rtype):
        assert qname == "_25._tcp.mail.example.com" and rtype == "TLSA"
        return [SimpleNamespace(to_text=lambda: "3 1 1 deadbeef")]

    monkeypatch.setattr(mta.resolver, "resolve", fake_resolve)
    res = mta.dane_tlsa("mail.example.com")
    assert res == ["3 1 1 deadbeef"]
