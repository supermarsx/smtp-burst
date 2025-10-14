from smtpburst import pipeline


def test_pipeline_send_email(monkeypatch):
    captured = {}

    def fake_bombing_mode(cfg, attachments=None):
        captured["server"] = cfg.SB_SERVER
        captured["sender"] = cfg.SB_SENDER
        captured["receivers"] = cfg.SB_RECEIVERS
        captured["subject"] = cfg.SB_SUBJECT
        captured["body"] = cfg.SB_BODY
        captured["trace_id"] = cfg.SB_TRACE_ID
        captured["trace_header"] = cfg.SB_TRACE_HEADER
        captured["emails"] = cfg.SB_SGEMAILS
        captured["bursts"] = cfg.SB_BURSTS
        captured["size"] = cfg.SB_SIZE

    monkeypatch.setattr(pipeline.send, "bombing_mode", fake_bombing_mode)

    steps = [
        {
            "action": "send_email",
            "server": "smtp.example.com:25",
            "sender": "a@b",
            "receivers": ["c@d"],
            "subject": "S",
            "body": "B",
            "trace_id": "T",
            "trace_header": "X-Trace",
        }
    ]
    runner = pipeline.PipelineRunner(steps)
    res = runner.run()
    assert res == [True]
    assert captured["server"] == "smtp.example.com:25"
    assert captured["sender"] == "a@b"
    assert captured["receivers"] == ["c@d"]
    assert captured["subject"] == "S" and captured["body"] == "B"
    assert captured["trace_id"] == "T" and captured["trace_header"] == "X-Trace"
    assert captured["emails"] == 1 and captured["bursts"] == 1 and captured["size"] == 0
