from smtpburst import pipeline


def test_pipeline_inbox_actions(monkeypatch):
    def fake_imap_search(
        host, user, password, criteria="ALL", port=993, ssl=True, mailbox="INBOX"
    ):
        return [b"1", b"2"]

    def fake_pop3_search(host, user, password, pattern=None, port=995, ssl=True):
        return [1]

    pipeline.register_action("imap_search", fake_imap_search)
    pipeline.register_action("pop3_search", fake_pop3_search)

    runner = pipeline.PipelineRunner(
        [
            {
                "action": "imap_search",
                "host": "imap.example.com:993",
                "user": "u",
                "password": "p",
                "criteria": "ALL",
            },
            {
                "action": "pop3_search",
                "host": "pop.example.com:995",
                "user": "u",
                "password": "p",
                "pattern": b"x",
            },
        ]
    )
    res = runner.run()
    assert res == [[b"1", b"2"], [1]]
