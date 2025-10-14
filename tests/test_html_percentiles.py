from smtpburst.reporting import html_report


def test_html_percentiles_section_for_numeric_lists():
    results = {"series": {"latency": [0.1, 0.2, 0.3, 0.4]}}
    html = html_report(results)
    assert "Percentiles" in html and "series.latency" in html
