import pytest
import smtpburst.send as send
from smtpburst.config import Config


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
