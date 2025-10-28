from __future__ import annotations

from typing import Iterable

# Re-export aggregated CLI options and argument→config map
from .core import CLI_OPTIONS as CORE_OPTIONS
from .discovery import CLI_OPTIONS as DISCOVERY_OPTIONS
from .mapping import MAP

CLIOption = tuple[tuple[str, ...], dict]

CLI_OPTIONS: Iterable[CLIOption] = [
    *CORE_OPTIONS,
    *DISCOVERY_OPTIONS,
]

__all__ = ["CLI_OPTIONS", "MAP"]
