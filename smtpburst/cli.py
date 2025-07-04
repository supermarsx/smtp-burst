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


def _add_core_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Options for basic email sending configuration."""
    parser.add_argument("--config", help="Path to JSON/YAML config file")
    parser.add_argument(
        "--pipeline-file",
        help="YAML file describing discovery/attack pipeline",
    )
    parser.add_argument(
        "--server",
        default=cfg.SB_SERVER,
        help="SMTP server to connect to",
    )
    parser.add_argument(
        "--sender",
        default=cfg.SB_SENDER,
        help="Envelope sender address",
    )
    parser.add_argument(
        "--receivers",
        nargs="+",
        default=cfg.SB_RECEIVERS,
        help="Space separated list of recipient addresses",
    )
    parser.add_argument(
        "--subject",
        default=cfg.SB_SUBJECT,
        help="Email subject line",
    )
    parser.add_argument("--body-file", help="File containing email body text")
    parser.add_argument(
        "--attach",
        nargs="+",
        metavar="FILE",
        help="Files to attach to each message",
    )


def _add_burst_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Options controlling burst behavior and delays."""
    parser.add_argument(
        "--emails-per-burst",
        type=int,
        default=cfg.SB_SGEMAILS,
        help="Number of emails per burst",
    )
    parser.add_argument(
        "--bursts", type=int, default=cfg.SB_BURSTS, help="Number of bursts to send"
    )
    parser.add_argument(
        "--email-delay",
        type=float,
        default=cfg.SB_SGEMAILSPSEC,
        help="Delay in seconds between individual emails",
    )
    parser.add_argument(
        "--burst-delay",
        type=float,
        default=cfg.SB_BURSTSPSEC,
        help="Delay in seconds between bursts",
    )
    parser.add_argument(
        "--global-delay",
        type=float,
        default=cfg.SB_GLOBAL_DELAY,
        help="Delay applied before any network action",
    )
    parser.add_argument(
        "--socket-delay",
        type=float,
        default=cfg.SB_OPEN_SOCKETS_DELAY,
        help="Delay between open socket checks",
    )
    parser.add_argument(
        "--tarpit-threshold",
        type=float,
        default=cfg.SB_TARPIT_THRESHOLD,
        help="Latency in seconds considered a tarpit",
    )


def _add_socket_options(parser: argparse.ArgumentParser) -> None:
    """Options for raw socket mode."""
    parser.add_argument(
        "--open-sockets",
        type=int,
        default=0,
        help="Open N TCP sockets and hold them open instead of sending email",
    )
    parser.add_argument(
        "--socket-duration",
        type=float,
        help="Close open sockets after SECONDS",
    )
    parser.add_argument(
        "--socket-iterations",
        type=int,
        help="Run the socket loop this many times before closing",
    )
    parser.add_argument(
        "--port", type=int, default=25, help="TCP port to use for socket mode"
    )


def _add_data_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Options controlling payload generation."""
    parser.add_argument(
        "--size",
        type=int,
        default=cfg.SB_SIZE,
        help="Random data size in bytes appended to each message",
    )
    parser.add_argument(
        "--data-mode",
        choices=["ascii", "binary", "utf8", "dict", "repeat"],
        default=cfg.SB_DATA_MODE,
        help="Payload generation mode",
    )
    parser.add_argument("--dict-file", help="Word list for dictionary mode")
    parser.add_argument(
        "--repeat-string",
        default=cfg.SB_REPEAT_STRING,
        help="String to repeat for repeat mode",
    )
    parser.add_argument(
        "--per-burst-data",
        action="store_true",
        default=cfg.SB_PER_BURST_DATA,
        help="Generate new data each burst",
    )
    parser.add_argument(
        "--secure-random",
        action="store_true",
        default=cfg.SB_SECURE_RANDOM,
        help="Use secure random generator",
    )
    parser.add_argument(
        "--rand-stream", help="Path to randomness stream for binary mode"
    )


def _add_message_mode_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Options toggling various message crafting tricks."""
    parser.add_argument(
        "--unicode-case-test",
        action="store_true",
        default=cfg.SB_TEST_UNICODE,
        help="Craft headers using Unicode/case tricks",
    )
    parser.add_argument(
        "--utf7-test",
        action="store_true",
        default=cfg.SB_TEST_UTF7,
        help="Encode message using UTF-7",
    )
    parser.add_argument(
        "--header-tunnel-test",
        action="store_true",
        default=cfg.SB_TEST_TUNNEL,
        help="Inject overlapping headers for tunneling",
    )
    parser.add_argument(
        "--control-char-test",
        action="store_true",
        default=cfg.SB_TEST_CONTROL,
        help="Insert encoded control characters",
    )


def _add_failure_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Options controlling behaviour on failure."""
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        default=cfg.SB_STOPFAIL,
        help="Stop execution when --stop-fail-count failures occur",
    )
    parser.add_argument(
        "--stop-fail-count",
        type=int,
        default=cfg.SB_STOPFQNT,
        help="Number of failed emails that triggers stopping",
    )


def _add_proxy_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """Proxy related options."""
    parser.add_argument(
        "--proxy-file", help="File containing SOCKS proxies to rotate through"
    )
    parser.add_argument(
        "--proxy-order",
        choices=["asc", "desc", "random"],
        default=cfg.SB_PROXY_ORDER,
        help="Order to apply proxies",
    )
    parser.add_argument(
        "--check-proxies",
        action="store_true",
        default=cfg.SB_CHECK_PROXIES,
        help="Validate proxies before use",
    )


def _add_auth_options(parser: argparse.ArgumentParser) -> None:
    """Authentication and enumeration related options."""
    parser.add_argument("--userlist", help="Username wordlist for SMTP AUTH")
    parser.add_argument("--passlist", help="Password wordlist for SMTP AUTH")
    parser.add_argument("--template-file", help="Phishing template file")
    parser.add_argument("--enum-list", help="Wordlist for enumeration")
    parser.add_argument("--vrfy-enum", action="store_true", help="Use VRFY to enumerate users")
    parser.add_argument("--expn-enum", action="store_true", help="Use EXPN to enumerate lists")
    parser.add_argument("--rcpt-enum", action="store_true", help="Use RCPT TO to enumerate users")
    parser.add_argument(
        "--login-test",
        action="store_true",
        help="Attempt SMTP AUTH logins using wordlists",
    )
    parser.add_argument(
        "--auth-test",
        action="store_true",
        help="Test advertised AUTH methods using --username/--password",
    )
    parser.add_argument("--username", help="Username for --auth-test")
    parser.add_argument("--password", help="Password for --auth-test")


def _add_security_options(parser: argparse.ArgumentParser, cfg: Config) -> None:
    """TLS related options."""
    parser.add_argument(
        "--ssl",
        action="store_true",
        default=cfg.SB_SSL,
        help="Use SMTPS (SSL/TLS) connection",
    )
    parser.add_argument(
        "--starttls",
        action="store_true",
        default=cfg.SB_STARTTLS,
        help="Issue STARTTLS after connecting",
    )


def _add_discovery_options(parser: argparse.ArgumentParser) -> None:
    """Options for discovery and testing commands."""
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
        "--tls-discovery",
        help="Host to probe TLS versions and certificate validity",
    )
    parser.add_argument(
        "--ssl-discovery",
        help="Host to discover supported legacy SSL versions",
    )
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
    parser.add_argument("--perf-test", help="Host to run performance test against")
    parser.add_argument("--baseline-host", help="Baseline host for performance comparison")
    parser.add_argument(
        "--rdns-test",
        action="store_true",
        help="Verify reverse DNS for the configured server",
    )
    parser.add_argument(
        "--banner-check",
        action="store_true",
        help="Read SMTP banner and verify reverse DNS",
    )
    parser.add_argument(
        "--outbound-test",
        action="store_true",
        help="Send one test email and exit",
    )


def _add_logging_options(parser: argparse.ArgumentParser) -> None:
    """Mutually exclusive logging level flags."""
    level_group = parser.add_mutually_exclusive_group()
    level_group.add_argument(
        "--silent", action="store_true", help="Suppress all log output"
    )
    level_group.add_argument(
        "--errors-only", action="store_true", help="Show only error messages"
    )
    level_group.add_argument(
        "--warnings", action="store_true", help="Show warnings and errors only"
    )


def build_parser(cfg: Config) -> argparse.ArgumentParser:
    """Return argument parser for smtp-burst."""
    parser = argparse.ArgumentParser(
        description="Send bursts of SMTP emails for testing purposes",
    )
    _add_core_options(parser, cfg)
    _add_burst_options(parser, cfg)
    _add_socket_options(parser)
    _add_data_options(parser, cfg)
    _add_message_mode_options(parser, cfg)
    _add_failure_options(parser, cfg)
    _add_proxy_options(parser, cfg)
    _add_auth_options(parser)
    _add_security_options(parser, cfg)
    _add_discovery_options(parser)
    _add_logging_options(parser)
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


def apply_args_to_config(cfg: Config, args: argparse.Namespace) -> None:
    """Map argument values onto Config attributes."""

    MAP = {
        "server": "SB_SERVER",
        "sender": "SB_SENDER",
        "receivers": "SB_RECEIVERS",
        "subject": "SB_SUBJECT",
        "emails_per_burst": "SB_SGEMAILS",
        "bursts": "SB_BURSTS",
        "email_delay": "SB_SGEMAILSPSEC",
        "burst_delay": "SB_BURSTSPSEC",
        "global_delay": "SB_GLOBAL_DELAY",
        "socket_delay": "SB_OPEN_SOCKETS_DELAY",
        "tarpit_threshold": "SB_TARPIT_THRESHOLD",
        "size": "SB_SIZE",
        "data_mode": "SB_DATA_MODE",
        "repeat_string": "SB_REPEAT_STRING",
        "per_burst_data": "SB_PER_BURST_DATA",
        "secure_random": "SB_SECURE_RANDOM",
        "unicode_case_test": "SB_TEST_UNICODE",
        "utf7_test": "SB_TEST_UTF7",
        "header_tunnel_test": "SB_TEST_TUNNEL",
        "control_char_test": "SB_TEST_CONTROL",
        "stop_on_fail": "SB_STOPFAIL",
        "stop_fail_count": "SB_STOPFQNT",
        "ssl": "SB_SSL",
        "starttls": "SB_STARTTLS",
        "proxy_order": "SB_PROXY_ORDER",
        "check_proxies": "SB_CHECK_PROXIES",
    }

    for arg_name, cfg_attr in MAP.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            setattr(cfg, cfg_attr, value)

