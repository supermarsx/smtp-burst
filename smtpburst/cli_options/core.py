from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from .. import __version__
from ..cli_core import positive_int, positive_float

try:
    import yaml  # noqa: F401
except ImportError:  # pragma: no cover - library may not be installed
    yaml = None  # type: ignore

CLIOption = Tuple[Tuple[str, ...], Dict[str, Any]]

# Core CLI options: config, sending, payload, async, logging, and reporting
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
    (("--server",), {"default_attr": "SB_SERVER", "help": "SMTP server to connect to"}),
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
        {"nargs": "+", "metavar": "FILE", "help": "Files to attach to each message"},
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
        ("--budget-seconds",),
        {
            "type": positive_float,
            "default_attr": "SB_BUDGET_SECONDS",
            "help": "Overall time budget in seconds for sends (0 disables)",
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
        {"type": positive_float, "help": "Close open sockets after SECONDS"},
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
        ("--profile",),
        {
            "choices": ["throughput", "latency", "mixed"],
            "help": "Apply a sending profile preset",
        },
    ),
    (
        ("--dict-file",),
        {"help": "Word list for dictionary mode (required with --data-mode dict)"},
    ),
    (
        ("--repeat-string",),
        {
            "default_attr": "SB_REPEAT_STRING",
            "help": (
                "String to repeat for repeat mode (required with --data-mode repeat)"
            ),
        },
    ),
    (("--trace-id",), {"help": "Set a trace ID header value on messages"}),
    (
        ("--trace-header",),
        {
            "default_attr": "SB_TRACE_HEADER",
            "help": "Header name to carry trace ID (default X-Burst-ID)",
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
        ("--long-headers-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_LONG_HEADERS",
            "help": "Craft very long headers to test folding",
        },
    ),
    (
        ("--nested-multipart-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_NESTED_MULTIPART",
            "help": "Generate nested multipart structure",
        },
    ),
    (
        ("--filename-trick-test",),
        {
            "action": "store_true",
            "default_attr": "SB_TEST_FILENAME_TRICK",
            "help": "Attach file with tricky filename (RLO)",
        },
    ),
    (
        ("--eicar-test",),
        {
            "action": "store_true",
            "default_attr": "SB_EICAR_TEST",
            "help": "Attach EICAR test string as a file",
        },
    ),
    (
        ("--smime-sample-test",),
        {
            "action": "store_true",
            "default_attr": "SB_SMIME_SAMPLE",
            "help": "Attach a sample S/MIME (PKCS#7) part",
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
    (
        ("--async",),
        {
            "dest": "async_mode",
            "action": "store_true",
            "help": "Enable asynchronous sending mode",
        },
    ),
    (
        ("--async-native",),
        {"action": "store_true", "help": "Use native aiosmtplib async mode"},
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
            "choices": ["ascii", "json", "yaml", "junit", "html", "jsonl", "prom"],
            "default": "ascii",
            "help": "Output report format",
        },
    ),
    (("--report-file",), {"metavar": "FILE", "help": "Write report to FILE"}),
]

__all__ = ["CLI_OPTIONS"]
