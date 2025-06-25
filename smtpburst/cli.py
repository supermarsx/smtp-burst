import argparse
import json
import warnings
from typing import Any, Dict

from .config import Config

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


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    """Return argument parser for smtp-burst."""
    parser = argparse.ArgumentParser(
        description="Send bursts of SMTP emails for testing purposes"
    )
    parser.add_argument("--config", help="Path to JSON/YAML config file")
    parser.add_argument("--server", default=cfg.SB_SERVER, help="SMTP server to connect to")
    parser.add_argument("--sender", default=cfg.SB_SENDER, help="Envelope sender address")
    parser.add_argument("--receivers", nargs="+", default=cfg.SB_RECEIVERS, help="Space separated list of recipient addresses")
    parser.add_argument("--subject", default=cfg.SB_SUBJECT, help="Email subject line")
    parser.add_argument("--body-file", help="File containing email body text")
    parser.add_argument("--emails-per-burst", type=int, default=cfg.SB_SGEMAILS, help="Number of emails per burst")
    parser.add_argument("--bursts", type=int, default=cfg.SB_BURSTS, help="Number of bursts to send")
    parser.add_argument("--email-delay", type=float, default=cfg.SB_SGEMAILSPSEC, help="Delay in seconds between individual emails")
    parser.add_argument("--burst-delay", type=float, default=cfg.SB_BURSTSPSEC, help="Delay in seconds between bursts")
    parser.add_argument("--open-sockets", type=int, default=0, help="Open N TCP sockets and hold them open instead of sending email")
    parser.add_argument("--port", type=int, default=25, help="TCP port to use for socket mode")
    parser.add_argument("--size", type=int, default=cfg.SB_SIZE, help="Random data size in bytes appended to each message")
    parser.add_argument("--data-mode", choices=["ascii", "binary", "utf8", "dict", "repeat"], default=cfg.SB_DATA_MODE, help="Payload generation mode")
    parser.add_argument("--dict-file", help="Word list for dictionary mode")
    parser.add_argument("--repeat-string", default=cfg.SB_REPEAT_STRING, help="String to repeat for repeat mode")
    parser.add_argument("--per-burst-data", action="store_true", default=cfg.SB_PER_BURST_DATA, help="Generate new data each burst")
    parser.add_argument("--secure-random", action="store_true", default=cfg.SB_SECURE_RANDOM, help="Use secure random generator")
    parser.add_argument("--rand-stream", help="Path to randomness stream for binary mode")
    parser.add_argument("--stop-on-fail", action="store_true", default=cfg.SB_STOPFAIL, help="Stop execution when --stop-fail-count failures occur")
    parser.add_argument("--stop-fail-count", type=int, default=cfg.SB_STOPFQNT, help="Number of failed emails that triggers stopping")
    parser.add_argument("--proxy-file", help="File containing SOCKS proxies to rotate through")
    parser.add_argument("--userlist", help="Username wordlist for SMTP AUTH")
    parser.add_argument("--passlist", help="Password wordlist for SMTP AUTH")
    parser.add_argument("--ssl", action="store_true", default=cfg.SB_SSL, help="Use SMTPS (SSL/TLS) connection")
    parser.add_argument("--starttls", action="store_true", default=cfg.SB_STARTTLS, help="Issue STARTTLS after connecting")
    parser.add_argument("--check-dmarc", help="Domain to query DMARC record for")
    parser.add_argument("--check-spf", help="Domain to query SPF record for")
    parser.add_argument("--check-dkim", help="Domain to query DKIM record for")
    parser.add_argument("--check-srv", help="Service to query SRV record for")
    parser.add_argument("--check-soa", help="Domain to query SOA record for")
    parser.add_argument("--check-txt", help="Domain to query TXT record for")
    parser.add_argument("--lookup-mx", help="Domain to query MX records for")
    parser.add_argument("--smtp-extensions", help="Host to discover SMTP extensions")
    parser.add_argument("--cert-check", help="Host to retrieve TLS certificate from")
    parser.add_argument(
        "--port-scan",
        nargs="+",
        help="Host followed by one or more ports to scan",
    )
    parser.add_argument("--probe-honeypot", help="Host to probe for SMTP honeypot")
    parser.add_argument(
        "--blacklist-check",
        nargs="+",
        help="IP followed by one or more DNSBL zones to query",
    )
    parser.add_argument(
        "--imap-check",
        nargs=4,
        metavar=("HOST", "USER", "PASS", "CRITERIA"),
        help="Check IMAP inbox for messages matching CRITERIA",
    )
    parser.add_argument(
        "--pop3-check",
        nargs=4,
        metavar=("HOST", "USER", "PASS", "PATTERN"),
        help="Check POP3 inbox for messages containing PATTERN",
    )
    parser.add_argument(
        "--open-relay-test",
        action="store_true",
        help="Test if the target SMTP server is an open relay",
    )
    parser.add_argument("--ping-test", help="Host to ping")
    parser.add_argument("--traceroute-test", help="Host to traceroute")
    level_group = parser.add_mutually_exclusive_group()
    level_group.add_argument("--silent", action="store_true", help="Suppress all log output")
    level_group.add_argument("--errors-only", action="store_true", help="Show only error messages")
    level_group.add_argument("--warnings", action="store_true", help="Show warnings and errors only")
    return parser


def parse_args(args=None, cfg: Config | None = None) -> argparse.Namespace:
    """Parse command line arguments, optionally merging a config file."""
    if cfg is None:
        cfg = Config()

    config_parser = argparse.ArgumentParser(add_help=False)
    config_parser.add_argument("--config")
    config_args, _ = config_parser.parse_known_args(args)

    parser = build_parser(cfg)
    if config_args.config:
        try:
            config_data = load_config(config_args.config)
        except FileNotFoundError:
            raise SystemExit(f"Config file not found: {config_args.config}")
        known = {action.dest for action in parser._actions}
        unknown = [k for k in config_data.keys() if k not in known]
        if unknown:
            warnings.warn(
                f"Unknown config options: {', '.join(unknown)}",
                RuntimeWarning,
            )
        parser.set_defaults(**config_data)
    return parser.parse_args(args)
