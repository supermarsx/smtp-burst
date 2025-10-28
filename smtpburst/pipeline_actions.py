from __future__ import annotations

from .config import Config
from . import send, attacks


def auth_matrix_action(
    server: str,
    *,
    username: str,
    password: str,
    ssl: bool = False,
    starttls: bool = False,
    helo_host: str | None = None,
    timeout: float = 10.0,
) -> dict[str, bool]:
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


def auth_matrix_full_action(
    server: str,
    *,
    username: str,
    password: str,
    mechanisms: list[str] | None = None,
    **kwargs,
) -> dict[str, bool]:
    base = auth_matrix_action(server, username=username, password=password, **kwargs)
    if mechanisms:
        return {m: bool(base.get(m)) for m in mechanisms}
    return base


def send_email_action(
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
    cfg.SB_SGEMAILS = 1
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    cfg.SB_SIZE = 0
    send.bombing_mode(cfg)
    return True


def performance_benchmark_action(
    host: str,
    iterations: int = 5,
    baseline: str | None = None,
    port: int | None = None,
) -> dict[str, dict[str, list[float]]]:
    h, p = send.parse_server(host)
    if port is not None:
        p = int(port)
    series: dict[str, list[float]] = {
        "connection_setup": [],
        "smtp_handshake": [],
        "message_send": [],
        "ping": [],
    }
    baseline_series: dict[str, list[float]] | None = None
    if baseline:
        baseline_series = {
            "connection_setup": [],
            "smtp_handshake": [],
            "message_send": [],
            "ping": [],
        }
    for _ in range(int(iterations)):
        res = attacks.performance_test(h, port=p, baseline=baseline)
        t = res.get("target", {})
        for k in series.keys():
            v = t.get(k)
            if isinstance(v, (int, float)):
                series[k].append(float(v))
        if baseline and baseline_series is not None:
            b = res.get("baseline", {})
            for k in baseline_series.keys():
                v = b.get(k)
                if isinstance(v, (int, float)):
                    baseline_series[k].append(float(v))
    out: dict[str, dict[str, list[float]]] = {"series": series}
    if baseline and baseline_series is not None:
        out["baseline_series"] = baseline_series
    return out


# Note: assertion and parallel helpers remain in pipeline.py to avoid circular deps
