import argparse
import json
import warnings
from typing import Any, Dict, Iterable, Tuple

from .config import Config

try:
    import yaml
except ImportError:  # pragma: no cover - library may not be installed
    yaml = None


CLIOption = Tuple[Tuple[str, ...], Dict[str, Any]]

# Each tuple contains positional flags and argument keyword options.  Any entry
# may include a ``default_attr`` key which maps to a ``Config`` attribute used
# for the default value.  A ``group`` key specifies the mutually exclusive
# logging group.
CLI_OPTIONS: Iterable[CLIOption] = [
    (("--config",), {"help": "Path to JSON/YAML config file"}),
    (("--pipeline-file",), {"help": "YAML file describing discovery/attack pipeline"}),
    (("--server",), {"default_attr": "SB_SERVER", "help": "SMTP server to connect to"}),
    (("--sender",), {"default_attr": "SB_SENDER", "help": "Envelope sender address"}),
    (("--receivers",), {
        "nargs": "+",
        "default_attr": "SB_RECEIVERS",
        "help": "Space separated list of recipient addresses",
    }),
    (("--subject",), {"default_attr": "SB_SUBJECT", "help": "Email subject line"}),
    (("--body-file",), {"help": "File containing email body text"}),
    (
        ("--attach",),
        {
            "nargs": "+",
            "metavar": "FILE",
            "help": "Files to attach to each message",
        },
    ),

    (("--emails-per-burst",), {
        "type": int,
        "default_attr": "SB_SGEMAILS",
        "help": "Number of emails per burst",
    }),
    (
        ("--bursts",),
        {
            "type": int,
            "default_attr": "SB_BURSTS",
            "help": "Number of bursts to send",
        },
    ),
    (("--email-delay",), {
        "type": float,
        "default_attr": "SB_SGEMAILSPSEC",
        "help": "Delay in seconds between individual emails",
    }),
    (("--burst-delay",), {
        "type": float,
        "default_attr": "SB_BURSTSPSEC",
        "help": "Delay in seconds between bursts",
    }),
    (("--global-delay",), {
        "type": float,
        "default_attr": "SB_GLOBAL_DELAY",
        "help": "Delay applied before any network action",
    }),
    (("--socket-delay",), {
        "type": float,
        "default_attr": "SB_OPEN_SOCKETS_DELAY",
        "help": "Delay between open socket checks",
    }),
    (("--tarpit-threshold",), {
        "type": float,
        "default_attr": "SB_TARPIT_THRESHOLD",
        "help": "Latency in seconds considered a tarpit",
    }),

    (("--open-sockets",), {
        "type": int,
        "default": 0,
        "help": "Open N TCP sockets and hold them open instead of sending email",
    }),
    (
        ("--socket-duration",),
        {
            "type": float,
            "help": "Close open sockets after SECONDS",
        },
    ),
    (
        ("--socket-iterations",),
        {
            "type": int,
            "help": "Run the socket loop this many times before closing",
        },
    ),
    (
        ("--port",),
        {
            "type": int,
            "default": 25,
            "help": "TCP port to use for socket mode",
        },
    ),

    (("--size",), {
        "type": int,
        "default_attr": "SB_SIZE",
        "help": "Random data size in bytes appended to each message",
    }),
    (("--data-mode",), {
        "choices": ["ascii", "binary", "utf8", "dict", "repeat"],
        "default_attr": "SB_DATA_MODE",
        "help": "Payload generation mode",
    }),
    (("--dict-file",), {"help": "Word list for dictionary mode"}),
    (
        ("--repeat-string",),
        {
            "default_attr": "SB_REPEAT_STRING",
            "help": "String to repeat for repeat mode",
        },
    ),
    (("--per-burst-data",), {
        "action": "store_true",
        "default_attr": "SB_PER_BURST_DATA",
        "help": "Generate new data each burst",
    }),
    (("--secure-random",), {
        "action": "store_true",
        "default_attr": "SB_SECURE_RANDOM",
        "help": "Use secure random generator",
    }),
    (("--rand-stream",), {"help": "Path to randomness stream for binary mode"}),

    (("--unicode-case-test",), {
        "action": "store_true",
        "default_attr": "SB_TEST_UNICODE",
        "help": "Craft headers using Unicode/case tricks",
    }),
    (("--utf7-test",), {
        "action": "store_true",
        "default_attr": "SB_TEST_UTF7",
        "help": "Encode message using UTF-7",
    }),
    (("--header-tunnel-test",), {
        "action": "store_true",
        "default_attr": "SB_TEST_TUNNEL",
        "help": "Inject overlapping headers for tunneling",
    }),
    (("--control-char-test",), {
        "action": "store_true",
        "default_attr": "SB_TEST_CONTROL",
        "help": "Insert encoded control characters",
    }),

    (("--stop-on-fail",), {
        "action": "store_true",
        "default_attr": "SB_STOPFAIL",
        "help": "Stop execution when --stop-fail-count failures occur",
    }),
    (("--stop-fail-count",), {
        "type": int,
        "default_attr": "SB_STOPFQNT",
        "help": "Number of failed emails that triggers stopping",
    }),

    (("--proxy-file",), {"help": "File containing SOCKS proxies to rotate through"}),
    (("--proxy-order",), {
        "choices": ["asc", "desc", "random"],
        "default_attr": "SB_PROXY_ORDER",
        "help": "Order to apply proxies",
    }),
    (("--check-proxies",), {
        "action": "store_true",
        "default_attr": "SB_CHECK_PROXIES",
        "help": "Validate proxies before use",
    }),

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

    (("--ssl",), {
        "action": "store_true",
        "default_attr": "SB_SSL",
        "help": "Use SMTPS (SSL/TLS) connection",
    }),
    (("--starttls",), {
        "action": "store_true",
        "default_attr": "SB_STARTTLS",
        "help": "Issue STARTTLS after connecting",
    }),

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
    (
        ("--blacklist-check",),
        {"nargs": "+", "help": "IP followed by one or more DNSBL zones to query"},
    ),
    (("--imap-check",), {
        "nargs": 4,
        "metavar": ("HOST", "USER", "PASS", "CRITERIA"),
        "help": "Check IMAP inbox for messages matching CRITERIA",
    }),
    (("--pop3-check",), {
        "nargs": 4,
        "metavar": ("HOST", "USER", "PASS", "PATTERN"),
        "help": "Check POP3 inbox for messages containing PATTERN",
    }),
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
        ("--traceroute-test",),
        {"help": "Host to traceroute"},
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

