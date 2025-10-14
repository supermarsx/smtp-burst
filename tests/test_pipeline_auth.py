from smtpburst import pipeline


def test_pipeline_auth_matrix(monkeypatch):
    called = {}

    def fake_auth_test(cfg):
        called["server"] = cfg.SB_SERVER
        called["user"] = cfg.SB_USERNAME
        called["ssl"] = cfg.SB_SSL
        return {"PLAIN": True}

    monkeypatch.setattr("smtpburst.send.auth_test", fake_auth_test)

    runner = pipeline.PipelineRunner(
        [
            {
                "action": "auth_matrix",
                "server": "h:25",
                "username": "u",
                "password": "p",
                "ssl": True,
            }
        ]
    )
    res = runner.run()
    assert res == [{"PLAIN": True}]
    assert (
        called["server"] == "h:25" and called["user"] == "u" and called["ssl"] is True
    )
