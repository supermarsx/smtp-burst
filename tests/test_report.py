import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst.report import ascii_report


def test_ascii_report_aligns_long_keys():
    data = {
        "short": 1,
        "veryverylongkey": 2,
        "mid": 3,
    }
    rep = ascii_report(data)
    lines = [l for l in rep.splitlines() if ':' in l]
    colon_positions = {line.index(':') for line in lines}
    assert len(colon_positions) == 1
    expected = len(max(data.keys(), key=len)) + 1
    assert colon_positions.pop() == expected
