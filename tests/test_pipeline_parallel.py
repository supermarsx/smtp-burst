from smtpburst import pipeline


def test_parallel_action_runs_steps_concurrently(monkeypatch):
    calls = []

    def a(x):
        calls.append(("a", x))
        return x + 1

    def b(y):
        calls.append(("b", y))
        return y * 2

    pipeline.register_action("inc", a)
    pipeline.register_action("mul", b)

    runner = pipeline.PipelineRunner(
        [
            {
                "action": "parallel",
                "steps": [
                    {"action": "inc", "x": 1},
                    {"action": "mul", "y": 2},
                ],
            }
        ]
    )
    res = runner.run()
    # One result which is the list from parallel action, order not guaranteed
    assert len(res) == 1 and isinstance(res[0], list)
    assert sorted(res[0]) == [2, 4]
