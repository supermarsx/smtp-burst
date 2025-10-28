from __future__ import annotations

import json
from typing import Any

from . import _flatten


def html_report(results: dict[str, Any]) -> str:
    rows: list[str] = []
    for name, data in results.items():
        pretty = (
            json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
        )
        rows.append(
            "<tr><td>" + str(name) + "</td><td><pre>" + pretty + "</pre></td></tr>"
        )
    table = "\n".join(rows)
    head = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>smtp-burst Report</title>"
        "<style>body{font-family:sans-serif}table{border-collapse:collapse}"
        "td,th{border:1px solid #ddd;padding:6px}th{background:#f4f4f4}</style>"
        "</head><body><h1>smtp-burst Report</h1>"
    )
    body = (
        "<table><thead><tr><th>Test</th><th>Result</th></tr></thead><tbody>"
        + table
        + "</tbody></table>"
    )

    def _section(title: str, inner: str) -> str:
        return f"<h2>{title}</h2>" + inner

    extra: list[str] = []
    perf = results.get("performance")
    if isinstance(perf, dict) and isinstance(perf.get("target"), dict):
        t = perf["target"]
        rows_t = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in t.items())
        extra.append(
            _section(
                "Performance (target)", "<table><tbody>" + rows_t + "</tbody></table>"
            )
        )
        try:
            vals = [float(v) for v in t.values()]
            mx = max(vals) if vals else 0.0
        except Exception:
            mx = 0.0
        if mx > 0:
            bar_rows: list[str] = []
            for k, v in t.items():
                try:
                    val = float(v)
                    width = int((val / mx) * 100)
                except Exception:
                    val, width = 0.0, 0
                outer = '<td><div style="background:#e8e8ff;width:100%;">'
                inner = (
                    f'<div style="background:#4f6bed;height:10px;width:{width}%"></div>'
                )
                label = f"<div><small>{val:.6f}</small></div>"
                row = (
                    "<tr><td>"
                    + str(k)
                    + "</td>"
                    + outer
                    + inner
                    + label
                    + "</div></td></tr>"
                )
                bar_rows.append(row)
            bars = (
                "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>"
                + "".join(bar_rows)
                + "</tbody></table>"
            )
            extra.append(_section("Performance Bars", bars))
        b = perf.get("baseline")
        if isinstance(b, dict):
            rows_b = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in b.items())
            extra.append(
                _section(
                    "Performance (baseline)",
                    "<table><tbody>" + rows_b + "</tbody></table>",
                )
            )
            keys = set(t.keys()) & set(b.keys())
            rows_d = "".join(
                f"<tr><td>{k}</td><td>{t[k] - b[k]:+0.6f}</td></tr>"
                for k in sorted(keys)
            )
            extra.append(
                _section(
                    "Performance (Δ target-baseline)",
                    "<table><tbody>" + rows_d + "</tbody></table>",
                )
            )
    # ESMTP summary
    es = results.get("esmtp")
    if isinstance(es, dict):
        feats = es.get("features")
        supports = es.get("supports") or {}
        tests = es.get("tests") or {}
        parts: list[str] = []
        if isinstance(feats, list):
            parts.append("<p>Features: " + ", ".join(map(str, feats)) + "</p>")
        if isinstance(supports, dict):
            rows = "".join(
                f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in supports.items()
            )
            parts.append("<h3>Supports</h3><table><tbody>" + rows + "</tbody></table>")
        if isinstance(tests, dict):
            rows = "".join(
                f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in tests.items()
            )
            parts.append("<h3>Tests</h3><table><tbody>" + rows + "</tbody></table>")
        if parts:
            extra_html = "".join(parts)
            body += _section("ESMTP", extra_html)

    tls = results.get("tls")
    if isinstance(tls, dict):
        rows = "".join(
            f"<tr><td>{ver}</td><td>{val}</td></tr>" for ver, val in tls.items()
        )
        extra.append(
            _section("TLS Versions", "<table><tbody>" + rows + "</tbody></table>")
        )
    st = results.get("starttls")
    if isinstance(st, dict):
        rows = "".join(
            f"<tr><td>{ver}</td><td>{val}</td></tr>" for ver, val in st.items()
        )
        extra.append(
            _section("STARTTLS Versions", "<table><tbody>" + rows + "</tbody></table>")
        )
    std = results.get("starttls_details")
    if isinstance(std, dict):
        rows = []
        for ver, info in std.items():
            if isinstance(info, dict):
                rows.append(
                    "<tr>"
                    f"<td>{ver}</td>"
                    f"<td>{info.get('supported')}</td>"
                    f"<td>{info.get('valid')}</td>"
                    f"<td>{info.get('protocol')}</td>"
                    f"<td>{info.get('cipher')}</td>"
                    "</tr>"
                )
        if rows:
            header = (
                "<thead><tr><th>Version</th><th>Supported</th><th>Valid</th>"
                "<th>Protocol</th><th>Cipher</th></tr></thead>"
            )
            extra.append(
                _section(
                    "STARTTLS Details",
                    "<table>" + header + "<tbody>" + "".join(rows) + "</tbody></table>",
                )
            )

    def _is_numeric_list(val: Any) -> bool:
        try:
            return isinstance(val, list) and all(
                isinstance(x, (int, float)) for x in val
            )
        except Exception:
            return False

    def _percentiles(vals: list[float]) -> dict[str, float]:
        if not vals:
            return {"p50": 0.0, "p90": 0.0, "p99": 0.0}
        s = sorted(float(v) for v in vals)
        import math

        def q(p):
            idx = max(0, min(len(s) - 1, math.ceil(p * len(s)) - 1))
            return s[idx]

        return {"p50": q(0.5), "p90": q(0.9), "p99": q(0.99)}

    pct_rows: list[str] = []
    for keys, val in _flatten(tuple(), results):
        if _is_numeric_list(val):
            pct = _percentiles(val)
            pct_rows.append(
                "<tr><td>"
                + ".".join(keys)
                + "</td>"
                + "".join(f"<td>{pct[k]:.6f}</td>" for k in ["p50", "p90", "p99"])
                + "</tr>"
            )
    extra_html = "".join(extra)
    if pct_rows:
        header = (
            "<thead><tr><th>Series</th><th>p50</th><th>p90</th><th>p99</th>"
            "</tr></thead>"
        )
        table_html = (
            "<table>" + header + "<tbody>" + "".join(pct_rows) + "</tbody></table>"
        )
        extra_html += _section("Percentiles", table_html)
    # MTA-STS and DANE/TLSA summaries
    mts = results.get("mta_sts")
    if isinstance(mts, list) and mts:
        items = "".join(f"<li>{str(x)}</li>" for x in mts)
        extra_html += _section("MTA-STS", "<ul>" + items + "</ul>")
    dane = results.get("dane_tlsa")
    if isinstance(dane, list) and dane:
        items = "".join(f"<li>{str(x)}</li>" for x in dane)
        extra_html += _section("DANE/TLSA", "<ul>" + items + "</ul>")
    bl = results.get("blacklist")
    if isinstance(bl, dict) and bl:
        rows = "".join(
            f"<tr><td>{zone}</td><td>{status}</td></tr>" for zone, status in bl.items()
        )
        extra_html += _section(
            "Blacklist Check", "<table><tbody>" + rows + "</tbody></table>"
        )
    am = results.get("auth_matrix") or results.get("auth")
    if isinstance(am, dict) and am:
        rows = "".join(
            f"<tr><td>{mech}</td><td>{ok}</td></tr>" for mech, ok in am.items()
        )
        extra_html += _section(
            "Auth Matrix", "<table><tbody>" + rows + "</tbody></table>"
        )
    tail = "</body></html>"
    return head + body + extra_html + tail


__all__ = ["html_report"]
