import subprocess

from smtpburst.discovery import nettests


def test_ping_timeout(monkeypatch):
    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")
    monkeypatch.setattr(nettests.shutil, "which", lambda x: "/bin/" + x)

    def fake_run(cmd, capture_output, text, check, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.ping("host", timeout=2) == "ping command timed out"


def test_traceroute_timeout(monkeypatch):
    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")
    monkeypatch.setattr(nettests.shutil, "which", lambda x: "/bin/" + x)

    def fake_run(cmd, capture_output, text, check, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    assert nettests.traceroute("host", timeout=2) == "traceroute command timed out"
