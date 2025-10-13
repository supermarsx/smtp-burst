import json
import smtpburst.reporting as reporting

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None

import pytest


def test_ascii_report_long_keys():
    results = {"short": 1, "this_is_a_really_long_key": 2}
    report = reporting.ascii_report(results)
    lines = report.splitlines()

    width = len("this_is_a_really_long_key")
    border = "+" + "-" * (width + 4) + "+"
    header = f"| {'Test Report':<{width + 2}} |"

    assert lines[0] == border
    assert lines[1] == header
    assert lines[2] == border
    assert lines[-1] == border
    assert lines[3] == f"| {'short':<{width}} | 1"
    assert lines[4] == f"| {'this_is_a_really_long_key':<{width}} | 2"


def test_json_report_valid():
    results = {"short": 1, "long": {"nested": 2}}
    output = reporting.json_report(results)
    assert json.loads(output) == results


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_yaml_report_valid():
    results = {"short": 1, "long": {"nested": 2}}
    output = reporting.yaml_report(results)
    assert yaml.safe_load(output) == results


def test_junit_counts_and_cases():
    results = {"ok": True, "bad": False, "obj": {"x": True, "y": False}}
    xml = reporting.junit_report(results)
    assert "<testsuite" in xml and 'tests="3"' in xml and 'failures="2"' in xml
    assert '<testcase name="ok"' in xml


def test_html_report_contains_rows():
    results = {"thing": {"a": 1}, "flag": False}
    html = reporting.html_report(results)
    assert "<table" in html and "thing" in html and "flag" in html
