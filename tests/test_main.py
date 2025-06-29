import os
import sys

# Ensure project root is on sys.path for imports

from smtpburst import __main__ as main_mod
from smtpburst import send
import logging


def test_main_open_sockets(monkeypatch):
    called = {}

    def fake_open(host, count, port, cfg=None, duration=None, iterations=None):
        called["args"] = (host, count, port, duration, iterations)

    monkeypatch.setattr(send, "open_sockets", fake_open)
    main_mod.main([
        "--open-sockets",
        "2",
        "--server",
        "host.example:2525",
        "--socket-duration",
        "1",
        "--socket-iterations",
        "3",
    ])
    assert called["args"] == ("host.example", 2, 2525, 1.0, 3)


def test_main_outbound_test(monkeypatch):
    calls = []

    def fake_send(cfg):
        calls.append("test")

    def fake_bomb(cfg):
        calls.append("bomb")

    monkeypatch.setattr(send, "send_test_email", fake_send)
    monkeypatch.setattr(send, "bombing_mode", fake_bomb)

    main_mod.main(["--outbound-test"])

    assert calls == ["test"]


def test_main_passes_attachments(monkeypatch, tmp_path):
    called = {}

    def fake_bomb(cfg, attachments=None):
        called["atts"] = attachments

    monkeypatch.setattr(send, "bombing_mode", fake_bomb)

    f = tmp_path / "a.txt"
    f.write_text("x")
    main_mod.main(["--attach", str(f)])

    assert called["atts"] == [str(f)]


def test_main_spawns_processes(monkeypatch):
    # Dummy Manager/Value implementation
    class DummyValue:
        def __init__(self, _type, value):
            self.value = value

    class DummyManager:
        def Value(self, typecode, value):
            return DummyValue(typecode, value)

    def manager_factory():
        return DummyManager()

    monkeypatch.setattr("multiprocessing.Manager", manager_factory)

    started = []
    joined = []

    class DummyProcess:
        def __init__(self, target=None, args=(), kwargs=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            started.append(self.args)

        def join(self):
            joined.append(self.args)

    monkeypatch.setattr("multiprocessing.Process", DummyProcess)

    monkeypatch.setattr(send, "time", type("T", (), {"sleep": lambda *a, **k: None}))
    monkeypatch.setattr(send, "appendMessage", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))

    main_mod.main(["--emails-per-burst", "2", "--bursts", "3"])

    assert len(started) == 6
    assert len(joined) == 6


def test_logging_modes(monkeypatch, caplog):
    def dummy_bombing_mode(cfg, attachments=None):
        log = logging.getLogger("smtpburst.send")
        log.info("info")
        log.warning("warn")
        log.error("err")

    monkeypatch.setattr(send, "bombing_mode", dummy_bombing_mode)

    caplog.set_level(logging.INFO)
    main_mod.main([])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" in msgs and "warn" in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--warnings"])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" not in msgs and "warn" in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--errors-only"])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" not in msgs and "warn" not in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--silent"])
    assert not caplog.records

def test_main_tls_discovery(monkeypatch):
    called = {}

    def fake_test(host, port):
        called['host'] = host
        called['port'] = port
        return {'TLSv1_2': {'supported': True}}

    def fake_report(res):
        called['report'] = res
        return 'R'

    monkeypatch.setattr(main_mod.send, 'parse_server', lambda s: ('h', 443))
    monkeypatch.setattr('smtpburst.tlstest.test_versions', fake_test)
    monkeypatch.setattr(main_mod, 'ascii_report', fake_report)

    main_mod.main(['--tls-discovery', 'h'])

    assert called['host'] == 'h'
    assert called['report'] == {'tls': {'TLSv1_2': {'supported': True}}}


def test_main_banner_check(monkeypatch):
    called = {}

    def fake_banner_check(server):
        called['server'] = server
        return ('banner', True)

    monkeypatch.setattr(main_mod.discovery, 'banner_check', fake_banner_check)

    main_mod.main(['--banner-check', '--server', 'srv'])

    assert called['server'] == 'srv'
