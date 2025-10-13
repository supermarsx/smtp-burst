from smtpburst import pipeline


def test_pipeline_variable_substitution(tmp_path):
    content = (
        "vars:\n"
        "  host: example.com\n"
        "steps:\n"
        "  - action: check_dmarc\n"
        "    domain: ${host}\n"
    )
    p = tmp_path / "p.yaml"
    p.write_text(content)
    # Monkeypatch action to capture substituted value
    called = {}

    def fake_check_dmarc(domain):
        called["domain"] = domain
        return True

    pipeline.register_action("check_dmarc", fake_check_dmarc)
    runner = pipeline.load_pipeline(str(p))
    runner.run()
    assert called["domain"] == "example.com"
