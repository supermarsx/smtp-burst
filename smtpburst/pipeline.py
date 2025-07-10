from __future__ import annotations

"""Simple pipeline runner for smtp-burst discovery and attack actions."""

from typing import Any, Dict, List, Callable
import logging

try:
    import yaml
except ImportError:  # pragma: no cover - optional dependency
    yaml = None

from . import send, attacks, discovery
from .discovery import nettests, tls_probe, ssl_probe

logger = logging.getLogger(__name__)


ACTION_MAP: Dict[str, Callable[..., Any]] = {
    "check_dmarc": discovery.check_dmarc,
    "check_spf": discovery.check_spf,
    "check_dkim": discovery.check_dkim,
    "check_srv": discovery.check_srv,
    "check_soa": discovery.check_soa,
    "check_txt": discovery.check_txt,
    "lookup_mx": discovery.lookup_mx,
    "smtp_extensions": discovery.smtp_extensions,
    "cert_check": discovery.check_certificate,
    "port_scan": discovery.port_scan,
    "probe_honeypot": discovery.probe_honeypot,
    "tls_discovery": tls_probe.discover,
    "ssl_discovery": ssl_probe.discover,
    "open_relay_test": nettests.open_relay_test,
    "ping": nettests.ping,
    "traceroute": nettests.traceroute,
    "vrfy_enum": nettests.vrfy_enum,
    "expn_enum": nettests.expn_enum,
    "rcpt_enum": nettests.rcpt_enum,
    "open_sockets": send.open_sockets,
    "send": send.bombing_mode,
    "tcp_syn_flood": attacks.tcp_syn_flood,
    "tcp_reset_attack": attacks.tcp_reset_attack,
    "tcp_reset_flood": attacks.tcp_reset_flood,
    "smurf_test": attacks.smurf_test,
}


class PipelineError(Exception):
    """Raised when pipeline loading fails."""


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
            kwargs = {k: v for k, v in step.items() if k != "action"}
            try:
                res = func(**kwargs)
                self.results.append(res)
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
    return PipelineRunner(
        steps,
        stop_on_fail=stop_on_fail,
        fail_threshold=fail_threshold,
    )
