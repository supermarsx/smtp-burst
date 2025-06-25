import os
import sys

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst import __main__ as main_mod
from smtpburst import send
import logging


def test_main_open_sockets(monkeypatch):
    called = {}
    def fake_open(host, count, port):
        called['args'] = (host, count, port)
    monkeypatch.setattr(send, 'open_sockets', fake_open)
    main_mod.main(['--open-sockets', '2', '--server', 'host.example:2525'])
    assert called['args'] == ('host.example', 2, 2525)


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
    monkeypatch.setattr('multiprocessing.Manager', manager_factory)

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
    monkeypatch.setattr('multiprocessing.Process', DummyProcess)

    monkeypatch.setattr(send, 'time', type('T', (), {'sleep': lambda *a, **k: None}))
    monkeypatch.setattr(send, 'appendMessage', lambda cfg: b'msg')
    monkeypatch.setattr(send, 'sizeof_fmt', lambda n: str(n))

    main_mod.main(['--emails-per-burst', '2', '--bursts', '3'])

    assert len(started) == 6
    assert len(joined) == 6


def test_logging_modes(monkeypatch, caplog):
    def dummy_bombing_mode(cfg):
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
