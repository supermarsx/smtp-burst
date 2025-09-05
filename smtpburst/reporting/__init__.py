"""Utilities for presenting smtp-burst results in various formats."""

from __future__ import annotations

from typing import Any, Dict, Callable
import json

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


REPORT_FORMATS: Dict[str, Callable[[Dict[str, Any]], str]] = {
    "ascii": ascii_report,
    "json": json_report,
    "yaml": yaml_report,
}

__all__ = ["ascii_report", "json_report", "yaml_report", "REPORT_FORMATS"]
