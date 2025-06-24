import argparse
import json
from typing import Any, Dict

import burstVars

try:
    import yaml
except ImportError:  # pragma: no cover - library may not be installed
    yaml = None


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


def build_parser():
    """Return argument parser for smtp-burst."""
    parser = argparse.ArgumentParser(
        description="Send bursts of SMTP emails for testing purposes"    )
    parser.add_argument(
        "--config",
        help="Path to JSON/YAML config file",
    )
    parser.add_argument(
        "--server",
        default=burstVars.SB_SERVER,
        help="SMTP server to connect to",
    )
    parser.add_argument(
        "--sender",
        default=burstVars.SB_SENDER,
        help="Envelope sender address",
    )
    parser.add_argument(
        "--receivers",
        nargs="+",
        default=burstVars.SB_RECEIVERS,
        help="Space separated list of recipient addresses",
    )
    parser.add_argument(
        "--emails-per-burst",
        type=int,
        default=burstVars.SB_SGEMAILS,
        help="Number of emails per burst",
    )
    parser.add_argument(
        "--bursts",
        type=int,
        default=burstVars.SB_BURSTS,
        help="Number of bursts to send",
    )
    parser.add_argument(
        "--email-delay",
        type=float,
        default=burstVars.SB_SGEMAILSPSEC,
        help="Delay in seconds between individual emails",
    )
    parser.add_argument(
        "--burst-delay",
        type=float,
        default=burstVars.SB_BURSTSPSEC,
        help="Delay in seconds between bursts",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=burstVars.SB_SIZE,
        help="Random data size in bytes appended to each message",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        default=burstVars.SB_STOPFAIL,
        help="Stop execution when --stop-fail-count failures occur",
    )
    parser.add_argument(
        "--stop-fail-count",
        type=int,
        default=burstVars.SB_STOPFQNT,
        help="Number of failed emails that triggers stopping",
    )
    return parser


def parse_args(args=None):
    """Parse command line arguments, optionally merging a config file."""
    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config")
    config_args, _ = config_parser.parse_known_args(args)

    parser = build_parser()
    if config_args.config:
        try:
            config_data = load_config(config_args.config)
        except FileNotFoundError:
            raise SystemExit(f"Config file not found: {config_args.config}")
        parser.set_defaults(**config_data)
    return parser.parse_args(args)

