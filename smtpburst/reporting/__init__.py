"""Utilities for presenting smtp-burst results in various formats."""

from __future__ import annotations

from typing import Any, Callable, Iterable
import json
import xml.etree.ElementTree as ET

try:  # pragma: no cover - optional dependency
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


def ascii_report(results: dict[str, Any]) -> str:
    """Return simple ASCII formatted report from ``results``."""

    width = max([len(k) for k in results] + [len("Test Report")])
    border = "+" + "-" * (width + 4) + "+"
    header = f"| {'Test Report':<{width + 2}} |"

    lines = [border, header, border]
    for name, data in results.items():
        lines.append(f"| {name:<{width}} | {data}")
    lines.append(border)
    return "\n".join(lines)


def json_report(results: dict[str, Any]) -> str:
    """Return results encoded as formatted JSON."""

    return json.dumps(results, indent=2, sort_keys=True)


def yaml_report(results: dict[str, Any]) -> str:
    """Return results encoded as YAML."""

    if yaml is None:
        raise RuntimeError("PyYAML not installed")
    # safe_dump adds a trailing newline which is not needed for logs
    return yaml.safe_dump(results, sort_keys=False).strip()


def _flatten(
    prefix: tuple[str, ...], value: Any
) -> Iterable[tuple[tuple[str, ...], Any]]:
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _flatten(prefix + (str(k),), v)
    else:
        yield prefix, value


def jsonl_report(results: dict[str, Any]) -> str:
    """Return results flattened as JSON Lines (one key=value per line).

    Keys are joined by dots, e.g., performance.target.ping
    """
    lines: list[str] = []
    for keys, val in _flatten(tuple(), results):
        key = ".".join(keys)
        try:
            sval = json.dumps(val)
        except Exception:
            sval = json.dumps(str(val))
        lines.append(f"{key}\t{sval}")
    return "\n".join(lines)


def _sanitize_metric_name(name: str) -> str:
    import re

    # Convert to lower, replace invalid chars with '_'
    s = name.lower()
    s = re.sub(r"[^a-z0-9_:]", "_", s)
    # Ensure does not start with digit
    if s and s[0].isdigit():
        s = "_" + s
    return s


def prometheus_report(results: dict[str, Any]) -> str:
    """Return a Prometheus-compatible metrics exposition of numeric leaves.

    Flattens numeric values and emits lines like:
      smtpburst_<key_path> <value>
    Non-numeric values are skipped.
    """
    lines: list[str] = []
    for keys, val in _flatten(tuple(), results):
        try:
            num = float(val)
        except (TypeError, ValueError):
            continue
        metric = _sanitize_metric_name("smtpburst_" + "_".join(keys))
        lines.append(f"{metric} {num}")
    return "\n".join(lines)


def junit_report(results: dict[str, Any]) -> str:
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


from .html import html_report  # noqa: E402


REPORT_FORMATS: dict[str, Callable[[dict[str, Any]], str]] = {
    "ascii": ascii_report,
    "json": json_report,
    "yaml": yaml_report,
    "junit": junit_report,
    "html": html_report,
    "jsonl": jsonl_report,
    "prom": prometheus_report,
}

__all__ = [
    "ascii_report",
    "json_report",
    "yaml_report",
    "junit_report",
    "html_report",
    "jsonl_report",
    "prometheus_report",
    "REPORT_FORMATS",
]
