import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import smtpburst.attacks as attacks


def test_performance_test(monkeypatch):
    monkeypatch.setattr(attacks, "connection_setup_time", lambda *a, **k: 0.1)
    monkeypatch.setattr(attacks, "smtp_handshake_time", lambda *a, **k: 0.2)
    monkeypatch.setattr(attacks, "message_send_time", lambda *a, **k: 0.3)
    monkeypatch.setattr(attacks, "ping_latency", lambda *a, **k: 0.4)

    res = attacks.performance_test("target", baseline="base:2525")

    expected = {
        "connection_setup": 0.1,
        "smtp_handshake": 0.2,
        "message_send": 0.3,
        "ping": 0.4,
    }

    assert res == {"target": expected, "baseline": expected}


def test_smurf_test_calls_ping(monkeypatch):
    ping_calls = []
    sleep_calls = []

    def fake_ping(host, count, timeout):
        ping_calls.append((host, count, timeout))
        return "ok"

    monkeypatch.setattr(attacks.nettests, "ping", fake_ping)
    monkeypatch.setattr(attacks.time, "sleep", lambda d: sleep_calls.append(d))

    attacks.smurf_test("t", 3, delay=0.05, timeout=2.0)

    assert ping_calls == [("t", 1, 2), ("t", 1, 2), ("t", 1, 2)]
    assert sleep_calls == [0.05, 0.05, 0.05]


def test_smurf_test_logs_failures(monkeypatch, caplog):
    def fake_ping(host, count, timeout):
        return {}

    monkeypatch.setattr(attacks.nettests, "ping", fake_ping)
    monkeypatch.setattr(attacks.time, "sleep", lambda _: None)

    with caplog.at_level("WARNING"):
        attacks.smurf_test("t", 2, delay=0, timeout=1)

    warnings = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warnings) == 2
    assert all("failed" in record.getMessage() for record in warnings)
