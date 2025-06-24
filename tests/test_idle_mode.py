import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import burstMain

class DummySocket:
    def __init__(self):
        self.closed = False
    def close(self):
        self.closed = True


def test_idle_socket_mode_opens_and_closes(monkeypatch):
    opened = []

    def fake_create_connection(addr):
        s = DummySocket()
        opened.append(s)
        return s

    monkeypatch.setattr(burstMain.socket, 'create_connection', fake_create_connection)
    monkeypatch.setattr(burstMain.signal, 'signal', lambda *args, **kwargs: None)
    monkeypatch.setattr(burstMain.time, 'sleep', lambda x: None)

    burstMain.idle_socket_mode(0.01)

    assert opened
    assert all(s.closed for s in opened)
