from smtpburst import send
from smtpburst.config import Config


def test_budget_seconds_stops_quickly(monkeypatch):
    submitted = []

    class DummyPool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def submit(self, fn, *args, **kwargs):
            submitted.append(args)

            class F:
                def result(self_inner):
                    return None

            return F()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(send, "ProcessPoolExecutor", DummyPool)
    monkeypatch.setattr(send, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))
    monkeypatch.setattr(send, "throttle", lambda cfg, delay=0.0: None)

    cfg = Config()
    cfg.SB_SGEMAILS = 100
    cfg.SB_BURSTS = 100
    cfg.SB_SIZE = 0
    cfg.SB_BUDGET_SECONDS = 0.000001  # very small budget should limit submissions
    send.bombing_mode(cfg)
    # Significantly fewer than total potential submissions
    assert len(submitted) < 10


def test_eicar_attachment_present():
    cfg = Config()
    cfg.SB_SIZE = 0
    cfg.SB_EICAR_TEST = True
    raw = send.append_message(cfg)
    text = raw.decode("utf-8", errors="ignore").lower()
    assert 'filename="eicar.com"' in text
