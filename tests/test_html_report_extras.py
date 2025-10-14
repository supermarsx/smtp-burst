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
