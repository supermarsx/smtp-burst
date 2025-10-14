from smtpburst import cli as burst_cli
from smtpburst.config import Config


def test_profile_throughput_applies():
    args = burst_cli.parse_args(["--profile", "throughput"], Config())
    cfg = Config()
    burst_cli.apply_args_to_config(cfg, args)
    assert cfg.SB_SGEMAILS == 10 and cfg.SB_BURSTS == 1
    assert cfg.SB_SGEMAILSPSEC == 0 and cfg.SB_BURSTSPSEC == 0 and cfg.SB_SIZE == 0
    assert cfg.SB_STOPFAIL is False and cfg.SB_RETRY_COUNT == 0


def test_profile_latency_applies():
    args = burst_cli.parse_args(["--profile", "latency"], Config())
    cfg = Config()
    burst_cli.apply_args_to_config(cfg, args)
    assert cfg.SB_SGEMAILS == 1 and cfg.SB_BURSTS == 5
    assert cfg.SB_SGEMAILSPSEC == 0.1 and cfg.SB_BURSTSPSEC == 0.5 and cfg.SB_SIZE == 0


def test_profile_mixed_applies():
    args = burst_cli.parse_args(["--profile", "mixed"], Config())
    cfg = Config()
    burst_cli.apply_args_to_config(cfg, args)
    assert cfg.SB_SGEMAILS == 3 and cfg.SB_BURSTS == 3
    assert cfg.SB_SIZE == 1024 and cfg.SB_PER_BURST_DATA is True
