# smtp-burst
Simple python script that sends smtp email in bursts using independent processes for each mail sent out. Used to test smtp capacity, handling and possible attack scenarios. Depends on `smtplib` and `multiprocessing`.

## Features

- Burst sending of emails across multiple processes
- Adjustable delays between emails and bursts
- Global and per-mode delay controls
- Tarpit detection based on response latency
- Stop automatically after a number of failed sends
- Optional JSON/YAML configuration file
- Open-only socket mode for connection tests
- Optional SSL or STARTTLS connections via CLI flags
- Random payload data appended to each message
- Customizable subject and message body via CLI options
- Autonomous bombing mode for hands-off bursts
- Helper scripts for packaging and running tests
- Discovery utilities for MX lookup, SMTP extension scan, certificate checks,
  port scanning and honeypot probing

## Installation

Python 3.11 or newer is required. Install the library directly from the
repository source:

```bash
$ pip install .
```

This will install the `smtp-burst` console entry point.

## Quick Start

1. Edit `smtpburst/config.py` as needed for your tests or override values on the
   command line.
2. Start testing by executing the package with optional CLI flags.

   ```bash
   $ python -m smtpburst --server smtp.example.com \
       --sender from@example.com --receivers to@example.com other@example.com \
       --subject "Test" --body-file body.txt
   ```

   Use `--ssl` for SMTPS or `--starttls` to upgrade the connection.
   Use `-h`/`--help` to see all available options.

An optional `--config` flag can load settings from a JSON or YAML file.
See `examples/config.yaml` for a reference.

## Command Line Options

Additional CLI flags provide extended functionality:

- `--open-sockets N` open N connections without sending email
- `--proxy-file FILE` rotate through SOCKS proxies in FILE
- `--proxy-order {asc,desc,random}` apply proxies in given order
- `--check-proxies` validate proxies before use
- `--userlist FILE` username wordlist for SMTP AUTH
- `--passlist FILE` password wordlist for SMTP AUTH
- `--template-file FILE` phishing template with `{sender}` tags
- `--enum-list FILE` addresses for directory harvest
- `--vrfy-enum` enumerate users with VRFY
- `--expn-enum` enumerate lists with EXPN
- `--rcpt-enum` enumerate via RCPT TO
- `--login-test` attempt SMTP AUTH logins using wordlists
- `--auth-test` test advertised SMTP AUTH mechanisms
- `--username USER` username for `--auth-test`
- `--password PASS` password for `--auth-test`
- `--ssl` connect using SMTPS
- `--starttls` upgrade the connection with STARTTLS
- `--check-dmarc DOMAIN` query DMARC record for DOMAIN
- `--check-spf DOMAIN` query SPF record for DOMAIN
- `--check-dkim DOMAIN` query DKIM record for DOMAIN
- `--check-srv NAME` query SRV record for NAME
- `--check-soa DOMAIN` query SOA record for DOMAIN
- `--check-txt DOMAIN` query TXT record for DOMAIN
- `--lookup-mx DOMAIN` lookup MX records for DOMAIN
- `--smtp-extensions HOST` list SMTP extensions for HOST
- `--cert-check HOST` retrieve TLS certificate from HOST
- `--port-scan HOST PORT [PORT ...]` scan ports on HOST
- `--probe-honeypot HOST` probe HOST for SMTP honeypot
- `--tls-discovery HOST` probe TLS versions and validate certificates on HOST
- `--ssl-discovery HOST` discover supported legacy SSL versions on HOST
- `--blacklist-check IP ZONE [ZONE ...]` check IP against DNSBL zones
- `--open-relay-test` test if the target SMTP server is an open relay
- `--ping-test HOST` run ping for HOST
- `--traceroute-test HOST` run traceroute to HOST
- `--perf-test HOST` measure connection, SMTP and ping performance for HOST
- `--baseline-host HOST` compare `--perf-test` results with HOST
- `--banner-check` read the SMTP banner and verify reverse DNS
- `--rdns-test` verify reverse DNS for the configured server
- `--outbound-test` send one test email and exit
- `--silent` suppress all output
- `--errors-only` show only error messages
- `--warnings` show warnings and errors only
- `--global-delay SECS` sleep SECS before each network action
- `--socket-delay SECS` delay between open socket checks
- `--socket-duration SECS` close open sockets after SECS
- `--socket-iterations N` run the socket loop N times and exit
- `--tarpit-threshold SECS` warn if responses exceed SECS
- `--unicode-case-test` craft headers using Unicode and case variation
- `--utf7-test` encode headers and body with UTF-7
- `--header-tunnel-test` add overlapping headers to test tunneling
- `--control-char-test` insert encoded control characters

Run `smtp-burst --help` for the complete list of options.

### Authentication Prerequisites

The `--login-test` and `--auth-test` options require credentials. Supply
wordlists with `--userlist` and `--passlist` or provide a single account using
`--username` and `--password` for `--auth-test`.

## Report Format

Discovery and network tests emit a small ASCII report. Example:

```
+-----------------+
| Test Report     |
+-----------------+
dmarc             : v=DMARC1; p=none
ping              : 64 bytes from 127.0.0.1
+-----------------+
```

Running TLS discovery prints the negotiated protocol and certificate status:

```
$ python -m smtpburst --tls-discovery smtp.example.com
+-----------------+
| Test Report     |
+-----------------+
tls               : {'TLSv1_2': {'supported': True, 'valid': False, 'protocol': 'TLSv1.2'}}
+-----------------+
```

Running legacy SSL discovery works similarly:

```
$ python -m smtpburst --ssl-discovery smtp.example.com
+-----------------+
| Test Report     |
+-----------------+
ssl               : {'SSLv3': False}
+-----------------+
```

Results are printed to standard output and can be redirected to a file if
required.

## Discovery Tests

The following flags perform DNS and network checks using the utilities in
`smtpburst.discovery` and `smtpburst.nettests`:

- `--check-dmarc`, `--check-spf`, `--check-dkim`
- `--check-srv`, `--check-soa`, `--check-txt`, `--lookup-mx`
- `--smtp-extensions`, `--cert-check`, `--port-scan`, `--probe-honeypot`,
  `--tls-discovery`, `--ssl-discovery`
- `--blacklist-check`
- `--open-relay-test`, `--ping-test`, `--traceroute-test`, `--perf-test`,
  `--baseline-host`, `--rdns-test`

When these options are used, the report shown above is generated.

## Examples

Verbose logging is enabled by default. To show only warnings:

```bash
$ python -m smtpburst --warnings --server smtp.example.com
```

Silent mode suppresses all logs:

```bash
$ python -m smtpburst --silent --server smtp.example.com
```

Send a quick outbound test email and exit:

```bash
$ python -m smtpburst --outbound-test --server smtp.example.com
```

Run a DNS check and save the report:

```bash
$ python -m smtpburst --check-dmarc example.com --ping-test example.com > report.txt
```

## Development

Install the additional tools for linting and running tests and install the
package in editable mode:

```bash
$ pip install -r requirements-dev.txt
$ pip install -e .
```

This installs `pytest` with coverage reporting, `ruff` for code style checks and
the optional dependencies (`dnspython` and `PyYAML`) so that the full test suite
can run.

## Running Tests

Execute the unit tests using the helper scripts:

```bash
$ ./scripts/run_tests.sh     # Unix-like systems
```

```batch
C:\> scripts\run_tests.bat   # Windows
```

The script simply invokes `pytest --cov` and collects coverage information.

## Packaging

Build standalone executables with [PyInstaller](https://www.pyinstaller.org/).
Use the platform specific build scripts located in `scripts/` to create a
standalone binary. Each script verifies that `pyinstaller` is available and
places the output in a platform specific `dist/` directory:

```bash
$ ./scripts/build_ubuntu.sh   # Linux
$ ./scripts/build_macos.sh    # macOS
```

```batch
C:\> scripts\build_windows.bat  % Windows
```

The resulting binaries will be placed in `dist/linux`, `dist/macos` or
`dist/windows` depending on the platform.

## License

Distributed under MIT License. See `license.md` for more information.

