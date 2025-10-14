"""Simple pipeline runner for smtp-burst discovery and attack actions."""

from __future__ import annotations

from typing import Any, Dict, List, Callable
import logging

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from . import send, attacks, discovery, inbox
from .config import Config
from .discovery import nettests, tls_probe, ssl_probe, starttls_probe, esmtp, mta

logger = logging.getLogger(__name__)


ACTION_MAP: Dict[str, Callable[..., Any]] = {}


def register_action(name: str, func: Callable[..., Any]) -> None:
    """Register ``func`` under ``name`` for use in pipelines."""

    ACTION_MAP[name] = func


# Register built-in actions
register_action("check_dmarc", discovery.check_dmarc)
register_action("check_spf", discovery.check_spf)
register_action("check_dkim", discovery.check_dkim)
register_action("check_srv", discovery.check_srv)
register_action("check_soa", discovery.check_soa)
register_action("check_txt", discovery.check_txt)
register_action("lookup_mx", discovery.lookup_mx)
register_action("smtp_extensions", discovery.smtp_extensions)
register_action("cert_check", discovery.check_certificate)
register_action("port_scan", discovery.port_scan)
register_action("async_port_scan", discovery.async_port_scan)
register_action("probe_honeypot", discovery.probe_honeypot)
register_action("banner_check", discovery.banner_check)
register_action("rdns_verify", discovery.rdns.verify)
register_action("tls_discovery", tls_probe.discover)
register_action("ssl_discovery", ssl_probe.discover)
register_action("starttls_discovery", starttls_probe.discover)
register_action("starttls_details", starttls_probe.details)
register_action("starttls_cipher_matrix", starttls_probe.cipher_matrix)
register_action("esmtp_check", esmtp.check)
register_action("mta_sts_policy", mta.mta_sts_policy)
register_action("dane_tlsa", mta.dane_tlsa)
register_action("imap_search", inbox.imap_search)
register_action("pop3_search", inbox.pop3_search)
register_action("imap_header_search", inbox.imap_header_search)


def _auth_matrix_action(
    server: str,
    *,
    username: str,
    password: str,
    ssl: bool = False,
    starttls: bool = False,
    helo_host: str | None = None,
    timeout: float = 10.0,
) -> dict[str, bool]:
    """Return mapping of AUTH mechanism to success for provided credentials."""
    cfg = Config()
    cfg.SB_SERVER = server
    cfg.SB_USERNAME = username
    cfg.SB_PASSWORD = password
    cfg.SB_SSL = bool(ssl)
    cfg.SB_STARTTLS = bool(starttls)
    cfg.SB_TIMEOUT = float(timeout)
    if helo_host:
        cfg.SB_HELO_HOST = helo_host
    return send.auth_test(cfg)


register_action("auth_matrix", _auth_matrix_action)
register_action("open_relay_test", nettests.open_relay_test)
register_action("blacklist_check", nettests.blacklist_check)
register_action("ping", nettests.ping)
register_action("traceroute", nettests.traceroute)
register_action("vrfy_enum", nettests.vrfy_enum)
register_action("expn_enum", nettests.expn_enum)
register_action("rcpt_enum", nettests.rcpt_enum)
register_action("open_sockets", send.open_sockets)
register_action("send", send.bombing_mode)


def _send_email_action(
    server: str,
    sender: str,
    receivers: list[str] | str,
    *,
    subject: str = "smtp-burst test",
    body: str = "smtp-burst message body",
    html_body: str | None = None,
    ssl: bool = False,
    starttls: bool = False,
    trace_id: str | None = None,
    trace_header: str = "X-Burst-ID",
) -> bool:
    cfg = Config()
    cfg.SB_SERVER = server
    cfg.SB_SENDER = sender
    cfg.SB_RECEIVERS = receivers if isinstance(receivers, list) else [receivers]
    cfg.SB_SUBJECT = subject
    cfg.SB_BODY = body
    if html_body:
        cfg.SB_HTML_BODY = html_body
    cfg.SB_SSL = bool(ssl)
    cfg.SB_STARTTLS = bool(starttls)
    if trace_id:
        cfg.SB_TRACE_ID = trace_id
        cfg.SB_TRACE_HEADER = trace_header or cfg.SB_TRACE_HEADER
    # ensure single message, no delays, no random payload
    cfg.SB_SGEMAILS = 1
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    cfg.SB_SIZE = 0
    send.bombing_mode(cfg)
    return True


register_action("send_email", _send_email_action)
register_action("tcp_syn_flood", attacks.tcp_syn_flood)
register_action("tcp_reset_attack", attacks.tcp_reset_attack)
register_action("tcp_reset_flood", attacks.tcp_reset_flood)
register_action("smurf_test", attacks.smurf_test)
register_action("performance_test", attacks.performance_test)


def _assert_action(**kwargs) -> bool:
    """Simple assertion action for pipelines.

    Supported keys (one per step):
    - equals: [left, right]
    - truthy: value
    - lt/le/gt/ge: [left, right]
    - ne: [left, right]
    Returns True on pass, False on failure.
    """

    def _get_pair(key: str):
        vals = kwargs.get(key)
        if not isinstance(vals, (list, tuple)) or len(vals) != 2:
            raise PipelineError(f"assert {key} requires a two-item list")
        return vals[0], vals[1]

    if "equals" in kwargs:
        a, b = _get_pair("equals")
        return a == b
    if "ne" in kwargs:
        a, b = _get_pair("ne")
        return a != b
    if "truthy" in kwargs:
        return bool(kwargs.get("truthy"))
    if "lt" in kwargs:
        a, b = _get_pair("lt")
        return a < b
    if "le" in kwargs:
        a, b = _get_pair("le")
        return a <= b
    if "gt" in kwargs:
        a, b = _get_pair("gt")
        return a > b
    if "ge" in kwargs:
        a, b = _get_pair("ge")
        return a >= b
    raise PipelineError(
        "assert step requires one of equals, ne, truthy, lt, le, gt, ge"
    )


register_action("assert", _assert_action)


def _parallel_action(steps: List[Dict[str, Any]]) -> List[Any]:
    """Run a list of pipeline steps in parallel using threads."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: List[Any] = []

    def run_step(step: Dict[str, Any]):
        if not isinstance(step, dict):
            raise PipelineError("parallel sub-step must be a mapping")
        action = step.get("action")
        if not action:
            raise PipelineError("parallel sub-step missing action")
        func = ACTION_MAP.get(action)
        if func is None:
            raise PipelineError(f"Unknown action: {action}")
        kwargs = {k: v for k, v in step.items() if k != "action"}
        return func(**kwargs)

    with ThreadPoolExecutor() as ex:
        futs = [ex.submit(run_step, s) for s in steps]
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as exc:  # pragma: no cover - runtime errors
                results.append(exc)
    return results


register_action("parallel", _parallel_action)


class PipelineError(Exception):
    """Raised when pipeline loading fails."""


def _substitute(value, vars: dict):
    from string import Template
    import re

    if isinstance(value, str):
        # Support simple ${var[key]} lookup for dicts
        m = re.fullmatch(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\[([^\]]+)\]\}", value)
        if m:
            var, key = m.group(1), m.group(2)
            base = vars.get(var)
            try:
                return base[key] if isinstance(base, dict) else value
            except Exception:
                return value
        try:
            return Template(value).safe_substitute(vars)
        except Exception:
            return value
    if isinstance(value, list):
        return [_substitute(v, vars) for v in value]
    if isinstance(value, dict):
        return {k: _substitute(v, vars) for k, v in value.items()}
    return value


class PipelineRunner:
    """Execute pipeline steps sequentially."""

    def __init__(
        self,
        steps: List[Dict[str, Any]],
        stop_on_fail: bool = False,
        fail_threshold: int = 1,
    ):
        self.steps = steps
        self.stop_on_fail = stop_on_fail
        self.fail_threshold = fail_threshold
        self.failures = 0
        self.results: List[Any] = []
        self.vars: Dict[str, Any] = {}

    def run(self) -> List[Any]:
        for step in self.steps:
            if not isinstance(step, dict):
                raise PipelineError("Step must be a mapping")
            action = step.get("action")
            if not action:
                raise PipelineError("Step missing action")
            func = ACTION_MAP.get(action)
            if func is None:
                raise PipelineError(f"Unknown action: {action}")
            kwargs = {k: v for k, v in step.items() if k not in {"action", "as"}}
            # Template substitution
            if self.vars:
                kwargs = _substitute(kwargs, self.vars)
            try:
                res = func(**kwargs)
                self.results.append(res)
                # Optional capture: if step specifies 'as', store the result in vars
                alias = step.get("as")
                if isinstance(alias, str) and alias:
                    self.vars[alias] = res
                success = not (isinstance(res, bool) and res is False)
            except Exception as exc:  # pragma: no cover - runtime errors
                logger.error("Action %s failed: %s", action, exc)
                success = False
                self.results.append(exc)
            if not success:
                self.failures += 1
                if self.stop_on_fail and self.failures >= self.fail_threshold:
                    break
        return self.results


def load_pipeline(path: str) -> PipelineRunner:
    """Load pipeline YAML file and return a :class:`PipelineRunner`."""
    if yaml is None:
        raise SystemExit("Pipeline feature requires PyYAML")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict) or "steps" not in data:
        raise PipelineError("Pipeline file must define a 'steps' list")
    steps = data.get("steps")
    if not isinstance(steps, list):
        raise PipelineError("'steps' must be a list")
    stop_on_fail = bool(data.get("stop_on_fail", False))
    fail_threshold = int(data.get("fail_threshold", 1))
    runner = PipelineRunner(
        steps,
        stop_on_fail=stop_on_fail,
        fail_threshold=fail_threshold,
    )
    # Load vars if provided
    if isinstance(data.get("vars"), dict):
        runner.vars = data.get("vars")
    return runner


def _assert_metrics_action(data: dict, checks: dict) -> bool:
    """Assert numeric metrics in ``data`` against ``checks``.

    ``checks`` format: { metric_name: { op: value } }, where op in
    {lt, le, gt, ge, eq, ne}. Returns True if all checks pass.
    """
    OPS = {
        "lt": lambda a, b: a < b,
        "le": lambda a, b: a <= b,
        "gt": lambda a, b: a > b,
        "ge": lambda a, b: a >= b,
        "eq": lambda a, b: a == b,
        "ne": lambda a, b: a != b,
    }
    ok = True
    for name, spec in (checks or {}).items():
        if name not in data:
            ok = False
            continue
        for op, val in spec.items():
            func = OPS.get(op)
            if func is None:
                ok = False
                continue
            try:
                if not func(float(data[name]), float(val)):
                    ok = False
            except Exception:
                ok = False
    return ok


register_action("assert_metrics", _assert_metrics_action)
