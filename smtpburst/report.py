from typing import Dict, Any


def ascii_report(results: Dict[str, Any]) -> str:
    """Return simple ASCII formatted report from ``results``."""
    width = max((len(name) for name in results), default=0)
    border = "+" + "-" * (width + 2) + "+"
    header = "| " + "Test Report".ljust(width) + " |"
    lines = [border, header, border]
    for name, data in results.items():
        lines.append(f"{name:<{width}} : {data}")
    lines.append(border)
    return "\n".join(lines)
