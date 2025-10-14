import pytest
from smtpburst import pipeline


def test_performance_benchmark_series(monkeypatch):
    calls = {"n": 0}

    def fake_perf(host, port=25, baseline=None):
        # Produce deterministic, increasing values per call
        i = calls["n"]
        calls["n"] += 1
        t = {
            "connection_setup": 0.1 + i * 0.01,
            "smtp_handshake": 0.2 + i * 0.01,
            "message_send": 0.3 + i * 0.01,
            "ping": 0.4 + i * 0.01,
        }
        res = {"target": t}
        if baseline:
            res["baseline"] = {k: v + 0.05 for k, v in t.items()}
        return res

    monkeypatch.setattr(pipeline.attacks, "performance_test", fake_perf)

    steps = [
        {
            "action": "performance_benchmark",
            "host": "smtp.example.com:25",
            "iterations": 3,
        }
    ]
    runner = pipeline.PipelineRunner(steps)
    res = runner.run()[0]
    seq = res["series"]["connection_setup"]
    assert len(seq) == 3
    assert seq[0] == 0.1 and seq[1] == 0.11 and seq[2] == pytest.approx(0.12)
    assert res["series"]["ping"][-1] == pytest.approx(0.42)
