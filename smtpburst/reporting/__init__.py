from typing import Dict, Any


def ascii_report(results: Dict[str, Any]) -> str:
    """Return simple ASCII formatted report from ``results``."""

    width = max([len(k) for k in results] + [len("Test Report")])
    border = "+" + "-" * (width + 2) + "+"
    header = "| " + "Test Report" + " " * (width - len("Test Report")) + " |"

    lines = [border, header, border]
    for name, data in results.items():
        lines.append(f"{name:<{width}}: {data}")
    lines.append(border)
    return "\n".join(lines)
