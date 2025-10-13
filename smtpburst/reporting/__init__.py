"""Utilities for presenting smtp-burst results in various formats."""

from __future__ import annotations

from typing import Any, Dict, Callable
import json
import xml.etree.ElementTree as ET

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def ascii_report(results: Dict[str, Any]) -> str:
    """Return simple ASCII formatted report from ``results``."""

    width = max([len(k) for k in results] + [len("Test Report")])
    border = "+" + "-" * (width + 4) + "+"
    header = f"| {'Test Report':<{width + 2}} |"

    lines = [border, header, border]
    for name, data in results.items():
        lines.append(f"| {name:<{width}} | {data}")
    lines.append(border)
    return "\n".join(lines)


def json_report(results: Dict[str, Any]) -> str:
    """Return results encoded as formatted JSON."""

    return json.dumps(results, indent=2, sort_keys=True)


def yaml_report(results: Dict[str, Any]) -> str:
    """Return results encoded as YAML."""

    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    # safe_dump adds a trailing newline which is not needed for logs
    return yaml.safe_dump(results, sort_keys=False).strip()


def junit_report(results: Dict[str, Any]) -> str:
    """Return results encoded as JUnit XML.

    A simple mapping is applied: each key in ``results`` becomes a testcase.
    Truthy values are treated as passing. Dictionaries with an ``error`` key or
    boolean ``False`` values are treated as failures with the error message
    included when possible.
    """
    suite = ET.Element("testsuite", name="smtpburst")
    failures = 0
    errors = 0
    total = 0
    for name, data in results.items():
        case = ET.SubElement(suite, "testcase", name=str(name))
        total += 1
        failed = False
        message = None
        if isinstance(data, dict):
            # Heuristic: failed if explicit error or any False value
            if "error" in data:
                failed = True
                message = str(data.get("error"))
            elif any(v is False for v in data.values()):
                failed = True
        elif data is False:
            failed = True
        if failed:
            fail = ET.SubElement(case, "failure")
            if message:
                fail.set("message", message)
            failures += 1
    suite.set("tests", str(total))
    suite.set("failures", str(failures))
    suite.set("errors", str(errors))
    return ET.tostring(suite, encoding="unicode")


def html_report(results: Dict[str, Any]) -> str:
    """Return a minimal HTML report for human-friendly viewing."""
    rows: list[str] = []
    for name, data in results.items():
        pretty = (
            json.dumps(data, indent=2)
            if isinstance(data, (dict, list))
            else str(data)
        )
        rows.append(
            "<tr><td>" + str(name) + "</td><td><pre>" + pretty + "</pre></td></tr>"
        )
    table = "\n".join(rows)
    head = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>smtp-burst Report</title>"
        "<style>body{font-family:sans-serif}"
        "table{border-collapse:collapse}"
        "td,th{border:1px solid #ddd;padding:6px}"
        "th{background:#f4f4f4}</style>"
        "</head><body><h1>smtp-burst Report</h1>"
    )
    body = (
        "<table><thead><tr><th>Test</th><th>Result</th></tr></thead><tbody>"
        + table
        + "</tbody></table>"
    )
    tail = "</body></html>"
    return head + body + tail


REPORT_FORMATS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "ascii": ascii_report,
    "json": json_report,
    "yaml": yaml_report,
    "junit": junit_report,
    "html": html_report,
}

__all__ = [
    "ascii_report",
    "json_report",
    "yaml_report",
    "junit_report",
    "html_report",
    "REPORT_FORMATS",
]
