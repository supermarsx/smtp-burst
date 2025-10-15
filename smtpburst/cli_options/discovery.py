from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from ..cli_core import positive_int

CLIOption = Tuple[Tuple[str, ...], Dict[str, Any]]

# Discovery, inbox, performance, and STARTTLS/TLS options
CLI_OPTIONS: Iterable[CLIOption] = [
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
    (("--probe-honeypot",), {"help": "Host to probe for SMTP honeypot"}),
    (
        ("--tls-discovery",),
        {"help": "Host to probe TLS versions and certificate validity"},
    ),
    (("--ssl-discovery",), {"help": "Host to discover supported legacy SSL versions"}),
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
    (("--ping-test",), {"help": "Host to ping"}),
    (
        ("--ping-timeout",),
        {"type": positive_int, "default": 1, "help": "Ping timeout in seconds"},
    ),
    (("--traceroute-test",), {"help": "Host to traceroute"}),
    (
        ("--traceroute-timeout",),
        {"type": positive_int, "default": 5, "help": "Traceroute timeout in seconds"},
    ),
    (("--perf-test",), {"help": "Host to run performance test against"}),
    (("--baseline-host",), {"help": "Baseline host for performance comparison"}),
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
    (("--userlist",), {"help": "Wordlist of usernames for enumeration/auth tests"}),
    (("--passlist",), {"help": "Wordlist of passwords for auth tests"}),
    (("--username",), {"help": "Username for login/auth tests"}),
    (("--password",), {"help": "Password for login/auth tests"}),
    (("--enum-list",), {"help": "Wordlist for VRFY/EXPN/RCPT enumeration"}),
    (("--vrfy-enum",), {"action": "store_true", "help": "Run VRFY enumeration"}),
    (("--expn-enum",), {"action": "store_true", "help": "Run EXPN enumeration"}),
    (("--rcpt-enum",), {"action": "store_true", "help": "Run RCPT TO enumeration"}),
    (
        ("--ssl",),
        {
            "action": "store_true",
            "default_attr": "SB_SSL",
            "help": "Use implicit TLS (SMTPS)",
        },
    ),
    (
        ("--starttls",),
        {
            "action": "store_true",
            "default_attr": "SB_STARTTLS",
            "help": "Upgrade to TLS via STARTTLS",
        },
    ),
    (("--template-file",), {"help": "Path to email body template (format string)"}),
    (
        ("--login-test",),
        {
            "action": "store_true",
            "help": "Attempt SMTP LOGIN with provided credentials",
        },
    ),
    (
        ("--auth-test",),
        {
            "action": "store_true",
            "help": "Test advertised AUTH mechanisms using provided credentials",
        },
    ),
    (("--auth-matrix",), {"help": "Host:port for AUTH matrix test"}),
    (
        ("--auth-mechs",),
        {"nargs": "+", "help": "Subset of AUTH mechanisms to include in matrix"},
    ),
]

__all__ = ["CLI_OPTIONS"]
