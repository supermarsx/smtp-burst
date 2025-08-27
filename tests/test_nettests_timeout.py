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


def test_ping_ipv6_prefers_ping6(monkeypatch):
    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")

    def which(cmd):
        return "/bin/" + cmd if cmd in {"ping", "ping6"} else None

    monkeypatch.setattr(nettests.shutil, "which", which)
    called = {}

    def fake_run(cmd, capture_output, text, check, timeout):
        called["cmd"] = cmd

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    nettests.ping("::1")
    assert called["cmd"][0] == "ping6"


def test_ping_ipv6_uses_dash6(monkeypatch):
    monkeypatch.setattr(nettests.platform, "system", lambda: "Linux")

    def which(cmd):
        return "/bin/" + cmd if cmd == "ping" else None

    monkeypatch.setattr(nettests.shutil, "which", which)
    called = {}

    def fake_run(cmd, capture_output, text, check, timeout):
        called["cmd"] = cmd

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    nettests.ping("2001:db8::1")
    assert called["cmd"][0] == "ping"
    assert "-6" in called["cmd"]


def test_ping_ipv6_windows(monkeypatch):
    monkeypatch.setattr(nettests.platform, "system", lambda: "Windows")
    monkeypatch.setattr(nettests.shutil, "which", lambda x: x)
    called = {}

    def fake_run(cmd, capture_output, text, check, timeout):
        called["cmd"] = cmd

        class Result:
            returncode = 0
            stdout = ""

        return Result()

    monkeypatch.setattr(nettests.subprocess, "run", fake_run)
    nettests.ping("fe80::1")
    assert called["cmd"][0] == "ping"
    assert "-6" in called["cmd"]
    assert "-n" in called["cmd"]
    assert "-w" in called["cmd"]
    assert called["cmd"][-1] == "fe80::1"
