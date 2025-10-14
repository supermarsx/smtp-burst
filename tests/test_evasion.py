from smtpburst.send import append_message
from smtpburst.config import Config


def test_long_headers_folding_present():
    cfg = Config()
    cfg.SB_SIZE = 0
    cfg.SB_TEST_LONG_HEADERS = True
    raw = append_message(cfg)
    # expect header present and folded continuation (newline + space)
    assert b"X-Long-Header:" in raw
    assert b"\n " in raw or b"\r\n " in raw


def test_nested_multipart_structure():
    cfg = Config()
    cfg.SB_SIZE = 0
    cfg.SB_TEST_NESTED_MULTIPART = True
    raw = append_message(cfg)
    text = raw.decode("utf-8", errors="ignore").lower()
    assert "multipart/mixed" in text and "multipart/alternative" in text


def test_filename_trick_rlo_attachment():
    cfg = Config()
    cfg.SB_SIZE = 0
    cfg.SB_TEST_FILENAME_TRICK = True
    raw = append_message(cfg)
    text = raw.decode("utf-8", errors="ignore")
    # filename parameter should be present and we expect 'exe' to appear
    assert "filename" in text and "exe" in text.lower()
