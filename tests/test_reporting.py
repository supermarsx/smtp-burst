import smtpburst.reporting as reporting


def test_ascii_report_long_keys():
    results = {"short": 1, "this_is_a_really_long_key": 2}
    report = reporting.ascii_report(results)
    lines = report.splitlines()

    width = len("this_is_a_really_long_key")
    border = "+" + "-" * (width + 2) + "+"
    header = "| Test Report" + " " * (width - len("Test Report")) + " |"

    assert lines[0] == border
    assert lines[1] == header
    assert lines[2] == border
    assert lines[-1] == border
    assert lines[3] == f"short{' ' * (width - len('short'))}: 1"
    assert lines[4] == f"this_is_a_really_long_key: 2"
