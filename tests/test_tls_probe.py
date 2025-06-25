import ssl
from smtpburst import tls_probe


def test_tls_discover(monkeypatch):
    class DummyRaw:
        def settimeout(self, t):
            pass
    def fake_socket():
        return DummyRaw()

    class DummyCtx:
        def __init__(self):
            self.minimum_version = None
            self.maximum_version = None
        def wrap_socket(self, sock, server_hostname=None):
            ver = self.maximum_version
            class DummySock:
                def __enter__(self_inner):
                    return self_inner
                def __exit__(self_inner, exc_type, exc, tb):
                    pass
                def connect(self_inner, addr):
                    if ver == ssl.TLSVersion.TLSv1_2:
                        return
                    raise OSError('fail')
            return DummySock()
    def fake_ctx_factory():
        return DummyCtx()

    monkeypatch.setattr(tls_probe.socket, 'socket', fake_socket)
    monkeypatch.setattr(tls_probe.ssl, 'create_default_context', fake_ctx_factory)

    res = tls_probe.discover('h')
    assert res['TLSv1'] is False
    assert res['TLSv1_1'] is False
    assert res['TLSv1_2'] is True
    assert res['TLSv1_3'] is False
