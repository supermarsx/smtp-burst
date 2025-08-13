import pytest
import smtpburst.send as send
from smtpburst.config import Config
import logging


def test_send_test_email(monkeypatch):
    calls = []

    def fake_sendmail(number, burst, counter, msg, cfg, **kwargs):
        calls.append((number, burst, counter.value, msg, cfg, kwargs))

    monkeypatch.setattr(send, "sendmail", fake_sendmail)

    cfg = Config()
    cfg.SB_SENDER = "a@b.com"
    cfg.SB_RECEIVERS = ["c@d.com", "e@f.com"]
    cfg.SB_SUBJECT = "Subj"

    send.send_test_email(cfg)

    assert len(calls) == 1
    number, burst, counter_val, msg, passed_cfg, kwargs = calls[0]
    expected = (
        f"From: {cfg.SB_SENDER}\n"
        f"To: {', '.join(cfg.SB_RECEIVERS)}\n"
        f"Subject: {cfg.SB_SUBJECT}\n\n"
        "smtp-burst outbound test\n"
    ).encode("utf-8")
    assert msg == expected
    assert passed_cfg is cfg


@pytest.mark.parametrize(
    "server,host,port",
    [
        ("127.0.0.1", "127.0.0.1", 25),
        ("127.0.0.1:2525", "127.0.0.1", 2525),
        ("[2001:db8::1]", "2001:db8::1", 25),
        ("[2001:db8::1]:587", "2001:db8::1", 587),
        ("bad:port", "bad", 25),
    ],
)
def test_parse_server_matrix(server, host, port):
    """Verify parse_server with IPv4, IPv6 and malformed inputs."""
    assert send.parse_server(server) == (host, port)


def test_append_message_missing_attachment(tmp_path, caplog):
    cfg = Config()
    cfg.SB_SIZE = 0
    missing = tmp_path / "missing.txt"
    with caplog.at_level(logging.WARNING):
        msg = send.append_message(cfg, attachments=[str(missing)])
    assert isinstance(msg, bytes)
    assert str(missing) in caplog.text
    assert missing.name not in msg.decode("utf-8", errors="ignore")


@pytest.mark.asyncio
async def test_async_bombing_mode(monkeypatch):
    """Async mode should send expected emails without spawning processes."""

    sent = []

    def fake_sendmail(number, burst, counter, msg, cfg, **kwargs):
        sent.append((number, burst, msg))

    monkeypatch.setattr(send, "sendmail", fake_sendmail)
    monkeypatch.setattr(send, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))

    import multiprocessing

    def boom(*args, **kwargs):  # pragma: no cover - should not be called
        raise AssertionError("Process should not be spawned in async mode")

    monkeypatch.setattr(multiprocessing, "Process", boom)

    cfg = Config()
    cfg.SB_SGEMAILS = 2
    cfg.SB_BURSTS = 1
    cfg.SB_SGEMAILSPSEC = 0
    cfg.SB_BURSTSPSEC = 0
    await send.async_bombing_mode(cfg)

    assert len(sent) == 2
    for number, burst, msg in sent:
        assert number in {1, 2}
        assert burst == 1
        assert msg == b"msg"
