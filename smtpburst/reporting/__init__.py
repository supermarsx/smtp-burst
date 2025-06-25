from typing import Dict, Any


def ascii_report(results: Dict[str, Any]) -> str:
    """Return simple ASCII formatted report from ``results``."""
    lines = ["+-----------------+", "| Test Report     |", "+-----------------+"]
    for name, data in results.items():
        lines.append(f"{name:20}: {data}")
    lines.append("+-----------------+")
    return "\n".join(lines)
