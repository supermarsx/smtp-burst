# project specification

`smtp-burst` sends bursts of SMTP emails for testing.  Development targets
Python 3.11.

## Development Requirements

Ensure the following commands succeed before submitting changes:

- `black --check .`
- `flake8`
- `pytest`

## Emerging Suite Directive

Evolve smtp-burst into a modular, multi-purpose SMTP testing suite. This
directive guides incremental PRs and merges; prefer small, cohesive changes
that expand capability while keeping tests green and style checks passing.

- Goal: modular suite with focused packs for sending, discovery, auth,
  TLS/security, inbox verification, content-evasion, resilience/DoS, and
  performance benchmarking.

- Core sending engine
  - Adopt true async sending via `aiosmtplib`, with connection reuse,
    pipelining tests, warm/cold start variants, retries with backoff/jitter,
    and concurrency caps per host.
  - Surface configuration toggles (`SB_ASYNC_WARM_START`,
    `SB_ASYNC_COLD_START`, `SB_ASYNC_THREAD_OFFLOAD`) so profiles can be
    exercised independently in tests.
  - Provide ready-made profiles (throughput, latency-sweep, mixed payloads).

- Protocol coverage
  - Validate ESMTP features: SIZE, 8BITMIME, SMTPUTF8, PIPELINING,
    CHUNKING/BDAT, DSN, and STARTTLS-required behavior (positive and negative
    cases).
  - Add STARTTLS version/cipher probing on SMTP ports (25/587) with hostname
    verification, complementing existing generic TLS scans.
  - Expand AUTH testing across mechanisms (PLAIN, LOGIN, CRAM-MD5, NTLM,
    XOAUTH2) using wordlists or provided creds.

- Security & discovery
  - Add MTA-STS and DANE/TLSA resolution and enforcement checks.
  - Broaden DNSBL checks with common zone bundles and parallel queries.
  - Enhance tarpit/greylisting detection and honeypot heuristics.

- Content & evasion
  - Extend beyond current unicode/UTF-7/header-tunnel/control-char tests to
    include folded/obs-fold headers, long lines, MIME boundary edge cases,
    nested multiparts, filename tricks, S/MIME samples, and EICAR variants.
  - Optional SpamAssassin integration and simple heuristics for spam scoring.

- End-to-end flows
  - “Send-then-verify” paths with unique message IDs/headers, IMAP/POP polling
    with timeouts/retries, and DSN/bounce parsing.

- Pipelines → test suites
  - Extend PipelineRunner with assertions (thresholds/boolean checks), gating,
    variables/templating, parallel steps, and plugin loading via entry points.

- Reporting
  - Add JUnit XML for CI, HTML reports with charts, JSONL/metrics streams.
  - Summaries: p50/p90/p99 latencies, error mix, capability matrices, baseline
    deltas.

- CLI/UX
  - Split flags into subcommands: `send`, `discovery`, `auth`, `suite`,
    `attack`, `inbox`. Ship example suites in `examples/`.

- Proxies
  - Detect schemes (`socks5://`, `http://`) and validate accordingly (use
    PySocks for SOCKS, HTTP CONNECT for HTTP). Support per-host proxy pools.

- Reliability & performance
  - Stage timeouts and budget-based cancellation; structured logging with
    correlation IDs; resource-safe socket handling and graceful shutdown.

- DX & testing
  - Embedded mock SMTP target for black-box tests; CI to run black/flake8/
    pytest on multiple platforms; align docs with chosen linter.

- Quick wins
  - Async sending via `aiosmtplib` + connection reuse.
  - STARTTLS probing on SMTP ports with cipher/version matrix.
  - Pipeline assertions and JUnit XML exporter.
  - Proxy scheme handling and correct validation.
  - End-to-end send-and-inbox verification step.
