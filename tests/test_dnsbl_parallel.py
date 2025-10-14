from smtpburst.discovery import nettests


def test_default_dnsbl_zones_contains_known():
    zones = nettests.default_dnsbl_zones()
    assert isinstance(zones, list) and "zen.spamhaus.org" in zones


def test_blacklist_check_parallel(monkeypatch):
    calls = []

    def fake_resolve(qname, rtype):
        calls.append(qname)
        if qname.endswith(".listed.example"):
            return [object()]
        raise nettests.resolver.NXDOMAIN

    monkeypatch.setattr(nettests.resolver, "resolve", fake_resolve)
    res = nettests.blacklist_check_parallel(
        "1.2.3.4", ["listed.example", "clean.example"], max_workers=2
    )
    assert res == {"listed.example": "listed", "clean.example": "not listed"}
    assert any(q.endswith("listed.example") for q in calls)
