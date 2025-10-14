from smtpburst import __main__ as main_mod


def test_main_auth_matrix_report(monkeypatch):
    called = {}

    def fake_parse_server(s):
        return ("host", 25)

    def fake_auth_test(cfg):
        return {"PLAIN": True, "LOGIN": False}

    def fake_report(res):
        called["res"] = res
        return "R"

    monkeypatch.setattr(main_mod.send, "parse_server", fake_parse_server)
    monkeypatch.setattr(main_mod.send, "auth_test", fake_auth_test)
    monkeypatch.setattr(main_mod, "ascii_report", fake_report)

    # Ensure it doesn't try to send anything else
    monkeypatch.setattr(
        main_mod.send, "bombing_mode", lambda cfg, attachments=None: None
    )

    main_mod.main(
        [
            "--auth-matrix",
            "smtp.example.com:25",
            "--username",
            "u",
            "--password",
            "p",
            "--auth-mechs",
            "PLAIN",
            "LOGIN",
        ]
    )
    assert called["res"] == {"auth_matrix": {"PLAIN": True, "LOGIN": False}}
