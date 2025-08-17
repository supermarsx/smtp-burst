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
    border = "+" + "-" * (width + 2) + "+"
    header = "| Test Report" + " " * (width - len("Test Report")) + " |"

    assert lines[0] == border
    assert lines[1] == header
    assert lines[2] == border
    assert lines[-1] == border
    assert lines[3] == f"short{' ' * (width - len('short'))}: 1"
    assert lines[4] == "this_is_a_really_long_key: 2"


def test_json_report_valid():
    results = {"short": 1, "long": {"nested": 2}}
    output = reporting.json_report(results)
    assert json.loads(output) == results


@pytest.mark.skipif(yaml is None, reason="PyYAML not installed")
def test_yaml_report_valid():
    results = {"short": 1, "long": {"nested": 2}}
    output = reporting.yaml_report(results)
    assert yaml.safe_load(output) == results
