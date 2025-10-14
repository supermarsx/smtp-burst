from __future__ import annotations

import argparse
import json
import warnings
from typing import Any, Dict, Iterable, Tuple

from .config import Config
from . import __version__

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

# Each tuple contains positional flags and argument keyword options.  Any entry
# may include a ``default_attr`` key which maps to a ``Config`` attribute used
# for the default value.  A ``group`` key specifies the mutually exclusive
# logging group.
CLI_OPTIONS: Iterable[CLIOption] = [
    (
        ("--version",),
        {
            "action": "version",
            "version": __version__,
            "help": "Show program version and exit",
        },
    ),
    (("--config",), {"help": "Path to JSON/YAML config file"}),
    (("--pipeline-file",), {"help": "YAML file describing discovery/attack pipeline"}),
    (
        ("--server",),
        {"default_attr": "SB_SERVER", "help": "SMTP server to connect to"},
    ),
    (
        ("--helo-host",),
        {"default_attr": "SB_HELO_HOST", "help": "Host to use in EHLO/HELO"},
    ),
    (("--sender",), {"default_attr": "SB_SENDER", "help": "Envelope sender address"}),
    (
        ("--receivers",),
        {
            "nargs": "+",
            "default_attr": "SB_RECEIVERS",
            "help": "Space separated list of recipient addresses",
        },
    ),
    (("--subject",), {"default_attr": "SB_SUBJECT", "help": "Email subject line"}),
    (("--body-file",), {"help": "File containing email body text"}),
    (("--html-body-file",), {"help": "File containing HTML body text"}),
    (
        ("--attach",),
        {
            "nargs": "+",
            "metavar": "FILE",
            "help": "Files to attach to each message",
        },
    ),
    (
        ("--emails-per-burst",),
        {
            "type": positive_int,
            "default_attr": "SB_SGEMAILS",
            "help": "Number of emails per burst",
        },
    ),
    (
        ("--bursts",),
        {
            "type": positive_int,
            "default_attr": "SB_BURSTS",
            "help": "Number of bursts to send",
        },
    ),
    (
        ("--email-delay",),
        {
            "type": positive_float,
            "default_attr": "SB_SGEMAILSPSEC",
            "help": "Delay in seconds between individual emails",
        },
    ),
    (
        ("--burst-delay",),
        {
            "type": positive_float,
            "default_attr": "SB_BURSTSPSEC",
            "help": "Delay in seconds between bursts",
        },
    ),
    (
        ("--global-delay",),
        {
            "type": positive_float,
            "default_attr": "SB_GLOBAL_DELAY",
            "help": "Delay applied before any network action",
        },
    ),
    (
        ("--socket-delay",),
        {
            "type": positive_float,
            "default_attr": "SB_OPEN_SOCKETS_DELAY",
            "help": "Delay between open socket checks",
        },
    ),
    (
        ("--tarpit-threshold",),
        {
            "type": positive_float,
            "default_attr": "SB_TARPIT_THRESHOLD",
            "help": "Latency in seconds considered a tarpit",
        },
    ),
    (
        ("--timeout",),
        {
            "type": positive_float,
            "default_attr": "SB_TIMEOUT",
            "help": "Timeout in seconds for network operations",
        },
    ),
    (
        ("--open-sockets",),
        {
            "type": positive_int,
            "default": 0,
            "help": "Open N TCP sockets and hold them open instead of sending email",
        },
    ),
    (
        ("--socket-duration",),
        {
            "type": positive_float,
            "help": "Close open sockets after SECONDS",
        },
    ),
    (
        ("--socket-iterations",),
        {
            "type": positive_int,
            "help": "Run the socket loop this many times before closing",
        },
    ),
    (
        ("--port",),
        {
            "type": positive_int,
            "default": 25,
            "help": "TCP port to use for socket mode",
        },
    ),
    (
        ("--size",),
        {
            "type": positive_int,
            "default_attr": "SB_SIZE",
            "help": "Random data size in bytes appended to each message",
        },
    ),
    (
        ("--data-mode",),
        {
            "choices": ["ascii", "binary", "utf8", "dict", "repeat"],
            "default_attr": "SB_DATA_MODE",
            "help": "Payload generation mode",
        },
    ),
    (
        ("--dict-file",),
        {"help": ("Word list for dictionary mode " "(required with --data-mode dict)")},
    ),
    (
        ("--repeat-string",),
        {
            "default_attr": "SB_REPEAT_STRING",
            "help": (
                "String to repeat for repeat mode " "(required with --data-mode repeat)"
            ),
        },
    ),
    (
        ("--per-burst-data",),
        {
            "action": "store_true",
            "default_attr": "SB_PER_BURST_DATA",
            "help": "Generate new data each burst",
        },
    ),
    (
        ("--secure-random",),
        {
            "action": "store_true",
            "default_attr": "SB_SECURE_RANDOM",
            "help": "Use secure random generator",
        },
    ),
    (("--rand-stream",), {"help": "Path to randomness stream for binary mode"}),
    (
        ("--unicode-case-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_UNICODE",
            "help": "Craft headers using Unicode/case tricks",
        },
    ),
    (
        ("--utf7-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_UTF7",
            "help": "Encode message using UTF-7",
        },
    ),
    (
        ("--header-tunnel-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_TUNNEL",
            "help": "Inject overlapping headers for tunneling",
        },
    ),
    (
        ("--control-char-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_CONTROL",
            "help": "Insert encoded control characters",
        },
    ),
    (
        ("--stop-on-fail",),
        {
            "action": "store_true",
            "default_attr": "SB_STOPFAIL",
            "help": "Stop execution when --stop-fail-count failures occur",
        },
    ),
    (
        ("--stop-fail-count",),
        {
            "type": positive_int,
            "default_attr": "SB_STOPFQNT",
            "help": "Number of failed emails that triggers stopping",
        },
    ),
    (
        ("--retry-count",),
        {
            "type": positive_int,
            "default_attr": "SB_RETRY_COUNT",
            "help": "Number of times to retry sending after failure",
        },
    ),
    (("--proxy-file",), {"help": "File containing SOCKS proxies to rotate through"}),
    (
        ("--proxy-order",),
        {
            "choices": ["asc", "desc", "random"],
            "default_attr": "SB_PROXY_ORDER",
            "help": "Order to apply proxies",
        },
    ),
    (
        ("--check-proxies",),
        {
            "action": "store_true",
            "default_attr": "SB_CHECK_PROXIES",
            "help": "Validate proxies before use",
        },
    ),
    (
        ("--proxy-timeout",),
        {
            "type": positive_float,
            "default_attr": "SB_PROXY_TIMEOUT",
            "help": "Timeout in seconds when validating proxies",
        },
    ),
    (("--userlist",), {"help": "Username wordlist for SMTP AUTH"}),
    (("--passlist",), {"help": "Password wordlist for SMTP AUTH"}),
    (("--template-file",), {"help": "Phishing template file"}),
    (("--enum-list",), {"help": "Wordlist for enumeration"}),
    (
        ("--vrfy-enum",),
        {"action": "store_true", "help": "Use VRFY to enumerate users"},
    ),
    (
        ("--expn-enum",),
        {"action": "store_true", "help": "Use EXPN to enumerate lists"},
    ),
    (
        ("--rcpt-enum",),
        {"action": "store_true", "help": "Use RCPT TO to enumerate users"},
    ),
    (
        ("--login-test",),
        {"action": "store_true", "help": "Attempt SMTP AUTH logins using wordlists"},
    ),
    (
        ("--auth-test",),
        {
            "action": "store_true",
            "help": "Test advertised AUTH methods using --username/--password",
        },
    ),
    (("--username",), {"help": "Username for --auth-test"}),
    (("--password",), {"help": "Password for --auth-test"}),
    (
        ("--ssl",),
        {
            "action": "store_true",
            "default_attr": "SB_SSL",
            "help": "Use SMTPS (SSL/TLS) connection",
        },
    ),
    (
        ("--starttls",),
        {
            "action": "store_true",
            "default_attr": "SB_STARTTLS",
            "help": "Issue STARTTLS after connecting",
        },
    ),
    (
        ("--async",),
        {
            "action": "store_true",
            "dest": "async_mode",
            "help": "Use asyncio-based sending",
        },
    ),
    (
        ("--async-native",),
        {
            "action": "store_true",
            "help": "Use native asyncio (aiosmtplib) sender",
        },
    ),
    (
        ("--async-max-concurrency",),
        {
            "type": positive_int,
            "metavar": "N",
            "help": "Max concurrent async sends (native mode)",
        },
    ),
    (
        ("--async-no-reuse",),
        {
            "action": "store_true",
            "help": "Disable connection reuse in native async mode",
        },
    ),
    (
        ("--async-pool-size",),
        {
            "type": positive_int,
            "metavar": "N",
            "help": "Connection pool size for native async mode",
        },
    ),
    (("--check-dmarc",), {"help": "Domain to query DMARC record for"}),
    (("--check-spf",), {"help": "Domain to query SPF record for"}),
    (("--check-dkim",), {"help": "Domain to query DKIM record for"}),
    (("--check-srv",), {"help": "Service to query SRV record for"}),
    (("--check-soa",), {"help": "Domain to query SOA record for"}),
    (("--check-txt",), {"help": "Domain to query TXT record for"}),
    (("--lookup-mx",), {"help": "Domain to query MX records for"}),
    (("--smtp-extensions",), {"help": "Host to discover SMTP extensions"}),
    (("--cert-check",), {"help": "Host to retrieve TLS certificate from"}),
    (
        ("--port-scan",),
        {"nargs": "+", "help": "Host followed by one or more ports to scan"},
    ),
    (
        ("--probe-honeypot",),
        {"help": "Host to probe for SMTP honeypot"},
    ),
    (
        ("--tls-discovery",),
        {"help": "Host to probe TLS versions and certificate validity"},
    ),
    (
        ("--ssl-discovery",),
        {"help": "Host to discover supported legacy SSL versions"},
    ),
    (("--starttls-discovery",), {"help": "Host to probe STARTTLS versions on SMTP"}),
    (
        ("--starttls-details",),
        {"help": "Host to collect STARTTLS version details on SMTP"},
    ),
    (("--esmtp-check",), {"help": "Host to check ESMTP features and simple tests"}),
    (("--mta-sts",), {"help": "Domain to check MTA-STS TXT policy for"}),
    (("--dane-tlsa",), {"help": "Host to query DANE/TLSA records for (SMTP)"}),
    (
        ("--blacklist-check",),
        {"nargs": "+", "help": "IP followed by one or more DNSBL zones to query"},
    ),
    (
        ("--imap-check",),
        {
            "nargs": 4,
            "metavar": ("HOST", "USER", "PASS", "CRITERIA"),
            "help": "Check IMAP inbox for messages matching CRITERIA",
        },
    ),
    (
        ("--pop3-check",),
        {
            "nargs": 4,
            "metavar": ("HOST", "USER", "PASS", "PATTERN"),
            "help": "Check POP3 inbox for messages containing PATTERN",
        },
    ),
    (
        ("--open-relay-test",),
        {
            "action": "store_true",
            "help": "Test if the target SMTP server is an open relay",
        },
    ),
    (
        ("--ping-test",),
        {"help": "Host to ping"},
    ),
    (
        ("--ping-timeout",),
        {"type": positive_int, "default": 1, "help": "Ping timeout in seconds"},
    ),
    (
        ("--traceroute-test",),
        {"help": "Host to traceroute"},
    ),
    (
        ("--traceroute-timeout",),
        {
            "type": positive_int,
            "default": 5,
            "help": "Traceroute timeout in seconds",
        },
    ),
    (
        ("--perf-test",),
        {"help": "Host to run performance test against"},
    ),
    (
        ("--baseline-host",),
        {"help": "Baseline host for performance comparison"},
    ),
    (
        ("--rdns-test",),
        {
            "action": "store_true",
            "help": "Verify reverse DNS for the configured server",
        },
    ),
    (
        ("--banner-check",),
        {"action": "store_true", "help": "Read SMTP banner and verify reverse DNS"},
    ),
    (
        ("--outbound-test",),
        {"action": "store_true", "help": "Send one test email and exit"},
    ),
    (
        ("--silent",),
        {"action": "store_true", "group": "log", "help": "Suppress all log output"},
    ),
    (
        ("--errors-only",),
        {"action": "store_true", "group": "log", "help": "Show only error messages"},
    ),
    (
        ("--warnings",),
        {
            "action": "store_true",
            "group": "log",
            "help": "Show warnings and errors only",
        },
    ),
    (
        ("--report-format",),
        {
            "choices": ["ascii", "json", "yaml", "junit", "html"],
            "default": "ascii",
            "help": "Output report format",
        },
    ),
    (("--report-file",), {"metavar": "FILE", "help": "Write report to FILE"}),
]


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
    for flags, options in CLI_OPTIONS:
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

    # Lightweight subcommand shim: if the first token is a known subcommand,
    # remove it from the argument list but record it on the returned Namespace
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
        # Derive known option names using the public parse_args API
        defaults = vars(parser.parse_args([]))
        unknown = [k for k in config_data.keys() if k not in defaults]
        if unknown:
            warnings.warn(
                f"Unknown config options: {', '.join(unknown)}",
                RuntimeWarning,
            )
        parser.set_defaults(**config_data)
    ns = parser.parse_args(raw_args)
    if subcmd:
        setattr(ns, "cmd", subcmd)
    return ns


def apply_args_to_config(cfg: Config, args: argparse.Namespace) -> None:
    """Map argument values onto Config attributes."""

    MAP = {
        "server": "SB_SERVER",
        "helo_host": "SB_HELO_HOST",
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
        "timeout": "SB_TIMEOUT",
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
        "retry_count": "SB_RETRY_COUNT",
        "ssl": "SB_SSL",
        "starttls": "SB_STARTTLS",
        "proxy_order": "SB_PROXY_ORDER",
        "check_proxies": "SB_CHECK_PROXIES",
        "proxy_timeout": "SB_PROXY_TIMEOUT",
        "html_body_file": "SB_HTML_BODY",
    }

    for arg_name, cfg_attr in MAP.items():
        value = getattr(args, arg_name, None)
        if value is not None:
            setattr(cfg, cfg_attr, value)

    # Native async options
    if getattr(args, "async_native", None):
        cfg.SB_ASYNC_NATIVE = True
    if getattr(args, "async_max_concurrency", None) is not None:
        cfg.SB_ASYNC_CONCURRENCY = int(args.async_max_concurrency)
    if getattr(args, "async_no_reuse", None):
        cfg.SB_ASYNC_REUSE = False
    if getattr(args, "async_pool_size", None) is not None:
        cfg.SB_ASYNC_POOL_SIZE = int(args.async_pool_size)
