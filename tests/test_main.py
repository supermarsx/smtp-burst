import os
import sys

# Ensure project root is on sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst import __main__ as main_mod
from smtpburst import send


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
    monkeypatch.setattr(main_mod, 'Manager', manager_factory)

    started = []
    joined = []
    class DummyProcess:
        def __init__(self, target=None, args=()):
            self.target = target
            self.args = args
        def start(self):
            started.append(self.args)
        def join(self):
            joined.append(self.args)
    monkeypatch.setattr(main_mod, 'Process', DummyProcess)

    monkeypatch.setattr(main_mod, 'time', type('T', (), {'sleep': lambda *a, **k: None}))
    monkeypatch.setattr(send, 'appendMessage', lambda cfg: b'msg')
    monkeypatch.setattr(send, 'sizeof_fmt', lambda n: str(n))

    main_mod.main(['--emails-per-burst', '2', '--bursts', '3'])

    assert len(started) == 6
    assert len(joined) == 6
