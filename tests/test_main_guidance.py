from smtpburst import __main__ as main_mod


def test_suite_subcommand_requires_pipeline(capsys, monkeypatch):
    # Stub out sending so no work is done if it would proceed
    monkeypatch.setattr(
        main_mod.send, "bombing_mode", lambda cfg, attachments=None: None
    )
    main_mod.main(["suite"])  # missing --pipeline-file
    out = capsys.readouterr().out
    assert "suite subcommand requires --pipeline-file" in out


def test_inbox_subcommand_requires_flags(capsys):
    main_mod.main(["inbox"])  # missing --imap-check/--pop3-check
    out = capsys.readouterr().out
    assert "inbox subcommand expects --imap-check or --pop3-check" in out
