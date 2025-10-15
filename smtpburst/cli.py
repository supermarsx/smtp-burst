from __future__ import annotations

from typing import Any  # noqa: F401

from .cli_core import (
    parse_args,
    build_parser,
    apply_args_to_config,
    positive_int,
    positive_float,
    load_config,
    yaml,
)
from .cli_options import CLI_OPTIONS  # re-export for external reference/tests
from .config import Config  # noqa: F401  (re-export type)

# This module is a thin façade that re-exports the public CLI API while keeping
# the bulk of option definitions and parser logic in smaller modules.

__all__ = [
    "parse_args",
    "build_parser",
    "apply_args_to_config",
    "positive_int",
    "positive_float",
    "load_config",
    "yaml",
    "CLI_OPTIONS",
    "Config",
]
