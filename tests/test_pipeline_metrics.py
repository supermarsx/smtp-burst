from smtpburst import pipeline


def test_pipeline_assert_metrics_with_store():
    # Simulated performance result
    perf = {
        "target": {
            "connection_setup": 0.1,
            "smtp_handshake": 0.2,
            "message_send": 0.3,
            "ping": 0.4,
        }
    }

    # Register a stub action that returns perf and store it as 'perf'
    def perf_action():
        return perf

    pipeline.register_action("perf_stub", lambda: perf)

    runner = pipeline.PipelineRunner(
        [
            {"action": "perf_stub", "as": "perf"},
            {
                "action": "assert_metrics",
                "data": "${perf[target]}",
                "checks": {"connection_setup": {"lt": 0.5}, "ping": {"le": 0.5}},
            },
        ]
    )
    res = runner.run()
    assert res == [perf, True]
