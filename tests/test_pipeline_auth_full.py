from smtpburst import pipeline


def test_auth_matrix_full_marks_missing(monkeypatch):
    def fake_auth_test(cfg):
        # Only PLAIN is supported/succeeds
        return {"PLAIN": True}

    monkeypatch.setattr("smtpburst.send.auth_test", fake_auth_test)

    steps = [
        {
            "action": "auth_matrix_full",
            "server": "smtp.example.com:25",
            "username": "u",
            "password": "p",
            "mechanisms": ["PLAIN", "LOGIN", "CRAM-MD5"],
        }
    ]
    res = pipeline.PipelineRunner(steps).run()[0]
    assert res == {"PLAIN": True, "LOGIN": False, "CRAM-MD5": False}
