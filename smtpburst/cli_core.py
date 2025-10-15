from __future__ import annotations

import argparse
import json
import warnings
from typing import Any, Dict, Tuple

from .config import Config

try:
    import yaml
except ImportError:  # pragma: no cover - library may not be installed
    yaml = None


def positive_int(value: str) -> int:
    """Return int from *value* ensuring it is positive."""
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return ivalue


def positive_float(value: str) -> float:
    """Return float from *value* ensuring it is positive."""
    fvalue = float(value)
    if fvalue <= 0:
        raise argparse.ArgumentTypeError("value must be > 0")
    return fvalue


CLIOption = Tuple[Tuple[str, ...], Dict[str, Any]]
SUBCOMMANDS = {"send", "discovery", "auth", "suite", "inbox", "attack"}

from .cli_options import (  # type: ignore  # noqa: E402
    CLI_OPTIONS as OPTS,
    MAP as ARG_MAP,
)


def load_config(path: str) -> Dict[str, Any]:
    """Load configuration from JSON or YAML file."""
    with open(path, "r", encoding="utf-8") as fh:
        if path.endswith((".yaml", ".yml")):
            if yaml is None:
                raise RuntimeError("PyYAML not installed")
            data = yaml.safe_load(fh) or {}
        else:
            data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("Config file must define a mapping of options")
    return data


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    """Return argument parser for smtp-burst."""
    parser = argparse.ArgumentParser(
        description="Send bursts of SMTP emails for testing purposes",
    )

    log_group = parser.add_mutually_exclusive_group()
    for flags, options in OPTS:
        opts = options.copy()
        group = opts.pop("group", None)
        attr = opts.pop("default_attr", None)
        if attr:
            opts.setdefault("default", getattr(cfg, attr))
        target = log_group if group == "log" else parser
        target.add_argument(*flags, **opts)

    return parser


def parse_args(args=None, cfg: Config | None = None) -> argparse.Namespace:
    """Parse command line arguments, optionally merging a config file."""
    if cfg is None:
        cfg = Config()

    # Subcommand capture
    raw_args = list(args) if args is not None else None
    subcmd = None
    if raw_args and raw_args[0] in SUBCOMMANDS:
        subcmd = raw_args.pop(0)

    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config")
    config_args, _ = config_parser.parse_known_args(raw_args)

    parser = build_parser(cfg)
    if config_args.config:
        try:
            config_data = load_config(config_args.config)
        except FileNotFoundError:
            raise SystemExit(f"Config file not found: {config_args.config}")
        defaults = vars(parser.parse_args([]))
        unknown = [k for k in config_data.keys() if k not in defaults]
        if unknown:
            warnings.warn(
                f"Unknown config options: {', '.join(unknown)}",
                RuntimeWarning,
            )
        parser.set_defaults(**config_data)

    # Subcommand-scoped help display
    if subcmd and raw_args and any(x in raw_args for x in ("-h", "--help")):
        sub = argparse.ArgumentParser(description=f"{subcmd} subcommand options")
        for flag in []:
            sub.add_argument(flag)
        sub.print_help()
        raise SystemExit(0)

    ns = parser.parse_args(raw_args)
    if subcmd:
        setattr(ns, "cmd", subcmd)
    return ns


def apply_args_to_config(cfg: Config, args: argparse.Namespace) -> None:
    """Map argument values onto Config attributes."""
    # Apply profile presets first so explicit flags can override them.
    profile = getattr(args, "profile", None)
    skip: set[str] = set()
    if profile == "throughput":
        cfg.SB_SGEMAILS = 10
        cfg.SB_BURSTS = 1
        cfg.SB_SGEMAILSPSEC = 0
        cfg.SB_BURSTSPSEC = 0
        cfg.SB_SIZE = 0
        cfg.SB_STOPFAIL = False
        cfg.SB_RETRY_COUNT = 0
        skip |= {
            "emails_per_burst",
            "bursts",
            "email_delay",
            "burst_delay",
            "size",
            "stop_on_fail",
            "retry_count",
        }
    elif profile == "latency":
        cfg.SB_SGEMAILS = 1
        cfg.SB_BURSTS = 5
        cfg.SB_SGEMAILSPSEC = 0.1
        cfg.SB_BURSTSPSEC = 0.5
        cfg.SB_SIZE = 0
        skip |= {"emails_per_burst", "bursts", "email_delay", "burst_delay", "size"}
    elif profile == "mixed":
        cfg.SB_SGEMAILS = 3
        cfg.SB_BURSTS = 3
        cfg.SB_SIZE = 1024
        cfg.SB_PER_BURST_DATA = True
        skip |= {"emails_per_burst", "bursts", "size", "per_burst_data"}

    for arg_name, cfg_attr in ARG_MAP.items():
        if profile and arg_name in skip:
            continue
        value = getattr(args, arg_name, None)
        if value is not None:
            setattr(cfg, cfg_attr, value)
