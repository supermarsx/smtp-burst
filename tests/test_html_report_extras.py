from smtpburst.reporting import html_report


def test_html_starttls_details_section():
    results = {
        "starttls_details": {
            "TLSv1_2": {
                "supported": True,
                "valid": True,
                "protocol": "TLSv1.2",
                "cipher": "ECDHE-RSA-AES128-GCM-SHA256",
            }
        }
    }
    html = html_report(results)
    assert "STARTTLS Details" in html and "ECDHE-RSA-AES128-GCM-SHA256" in html


def test_html_esmtp_and_mta_dane_sections():
    results = {
        "esmtp": {
            "features": ["size", "8bitmime"],
            "supports": {"size": True, "8bitmime": True},
            "tests": {"eight_bit_send": True, "size_enforced": True},
        },
        "mta_sts": ["v=STSv1; id=1"],
        "dane_tlsa": ["3 1 1 deadbeef"],
    }
    html = html_report(results)
    assert (
        "ESMTP" in html
        and "eight_bit_send" in html
        and "MTA-STS" in html
        and "DANE/TLSA" in html
    )


def test_html_blacklist_and_auth_sections():
    results = {
        "blacklist": {"zen.spamhaus.org": "not listed", "bl.example": "listed"},
        "auth_matrix": {"PLAIN": True, "LOGIN": False},
    }
    html = html_report(results)
    assert "Blacklist Check" in html and "zen.spamhaus.org" in html
    assert "Auth Matrix" in html and "LOGIN" in html
