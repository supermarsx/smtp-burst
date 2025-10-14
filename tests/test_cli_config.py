import argparse
import json
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import cli as burst_cli
from smtpburst.config import Config
from smtpburst import __version__

import logging
from smtpburst import __main__ as main_mod


def test_json_config_parsing(tmp_path):
    cfg = {"server": "json.example.com", "bursts": 2}
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))

    args = burst_cli.parse_args(["--config", str(cfg_path)], Config())
    assert args.server == "json.example.com"
    assert args.bursts == 2


def test_cli_overrides_config(tmp_path):
    cfg = {"server": "should.be.overridden"}
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps(cfg))

    args = burst_cli.parse_args(
        ["--config", str(cfg_path), "--server", "cli.example.com"], Config()
    )
    assert args.server == "cli.example.com"


@pytest.mark.skipif(burst_cli.yaml is None, reason="PyYAML not installed")
def test_yaml_config_parsing(tmp_path):
    yaml_cfg = "server: yaml.example.com\n"
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml_cfg)

    args = burst_cli.parse_args(["--config", str(cfg_path)], Config())
    assert args.server == "yaml.example.com"


def test_open_sockets_option():
    args = burst_cli.parse_args(["--open-sockets", "5"], Config())
    assert args.open_sockets == 5


def test_socket_duration_option():
    args = burst_cli.parse_args(["--socket-duration", "4"], Config())
    assert args.socket_duration == 4


def test_socket_iterations_option():
    args = burst_cli.parse_args(["--socket-iterations", "3"], Config())
    assert args.socket_iterations == 3


@pytest.mark.parametrize(
    "flag",
    [
        "--emails-per-burst",
        "--bursts",
        "--open-sockets",
        "--socket-iterations",
        "--port",
        "--size",
        "--stop-fail-count",
        "--retry-count",
        "--ping-timeout",
        "--traceroute-timeout",
    ],
)
def test_negative_int_options(flag):
    with pytest.raises(SystemExit):
        burst_cli.parse_args([flag, "-1"], Config())


@pytest.mark.parametrize(
    "flag",
    [
        "--email-delay",
        "--burst-delay",
        "--global-delay",
        "--socket-delay",
        "--tarpit-threshold",
        "--timeout",
        "--socket-duration",
        "--proxy-timeout",
    ],
)
def test_negative_float_options(flag):
    with pytest.raises(SystemExit):
        burst_cli.parse_args([flag, "-0.1"], Config())


def test_proxy_file_option(tmp_path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("127.0.0.1:1080\n")
    args = burst_cli.parse_args(["--proxy-file", str(proxy_file)], Config())
    assert args.proxy_file == str(proxy_file)


def test_ssl_flag():
    args = burst_cli.parse_args(["--ssl"], Config())
    assert args.ssl


def test_starttls_flag():
    args = burst_cli.parse_args(["--starttls"], Config())
    assert args.starttls


def test_helo_host_option():
    args = burst_cli.parse_args(["--helo-host", "ehlo.example"], Config())
    assert args.helo_host == "ehlo.example"
    cfg = Config()
    burst_cli.apply_args_to_config(cfg, args)
    assert cfg.SB_HELO_HOST == "ehlo.example"


def test_subject_option():
    args = burst_cli.parse_args(["--subject", "MySub"], Config())
    assert args.subject == "MySub"


def test_body_file_option(tmp_path):
    body_file = tmp_path / "body.txt"
    body_file.write_text("hello")
    args = burst_cli.parse_args(["--body-file", str(body_file)], Config())
    assert args.body_file == str(body_file)


def test_html_body_file_option(tmp_path):
    body_file = tmp_path / "body.html"
    body_file.write_text("<p>hello</p>")
    args = burst_cli.parse_args(["--html-body-file", str(body_file)], Config())
    assert args.html_body_file == str(body_file)


def test_attach_option(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("a")
    f2.write_text("b")
    args = burst_cli.parse_args(["--attach", str(f1), str(f2)], Config())
    assert args.attach == [str(f1), str(f2)]


def test_data_mode_option():
    args = burst_cli.parse_args(["--data-mode", "binary"], Config())
    assert args.data_mode == "binary"


def test_new_delay_options():
    args = burst_cli.parse_args(
        [
            "--global-delay",
            "1",
            "--socket-delay",
            "2",
            "--tarpit-threshold",
            "3",
        ],
        Config(),
    )
    assert args.global_delay == 1
    assert args.socket_delay == 2
    assert args.tarpit_threshold == 3


def test_timeout_applies_to_config():
    args = burst_cli.parse_args(["--timeout", "7"], Config())
    cfg = Config()
    burst_cli.apply_args_to_config(cfg, args)
    assert cfg.SB_TIMEOUT == 7


def test_per_burst_flag():
    args = burst_cli.parse_args(["--per-burst-data"], Config())
    assert args.per_burst_data


def test_discovery_options():
    args = burst_cli.parse_args(
        [
            "--check-dmarc",
            "ex.com",
            "--ping-test",
            "host",
            "--ping-timeout",
            "4",
            "--traceroute-test",
            "thost",
            "--traceroute-timeout",
            "6",
        ],
        Config(),
    )
    assert args.check_dmarc == "ex.com"
    assert args.ping_test == "host"
    assert args.ping_timeout == 4
    assert args.traceroute_test == "thost"
    assert args.traceroute_timeout == 6


def test_perf_cli_options():
    args = burst_cli.parse_args(
        ["--perf-test", "host", "--baseline-host", "base"], Config()
    )
    assert args.perf_test == "host"
    assert args.baseline_host == "base"


def test_blacklist_option():
    args = burst_cli.parse_args(
        ["--blacklist-check", "1.2.3.4", "rbl.example"], Config()
    )
    assert args.blacklist_check == ["1.2.3.4", "rbl.example"]


def test_open_relay_flag():
    args = burst_cli.parse_args(["--open-relay-test"], Config())
    assert args.open_relay_test


def test_new_discovery_cli_options():
    args = burst_cli.parse_args(
        [
            "--lookup-mx",
            "example.com",
            "--smtp-extensions",
            "host",
            "--cert-check",
            "host",
            "--port-scan",
            "host",
            "25",
            "587",
            "--probe-honeypot",
            "host",
        ],
        Config(),
    )
    assert args.lookup_mx == "example.com"
    assert args.smtp_extensions == "host"
    assert args.cert_check == "host"
    assert args.port_scan == ["host", "25", "587"]
    assert args.probe_honeypot == "host"


def test_tls_discovery_option():
    args = burst_cli.parse_args(["--tls-discovery", "host"], Config())
    assert args.tls_discovery == "host"


def test_ssl_discovery_option():
    args = burst_cli.parse_args(["--ssl-discovery", "host"], Config())
    assert args.ssl_discovery == "host"


def test_starttls_discovery_option():
    args = burst_cli.parse_args(["--starttls-discovery", "host"], Config())
    assert args.starttls_discovery == "host"


def test_async_native_cli_flags():
    args = burst_cli.parse_args(
        [
            "--async",
            "--async-native",
            "--async-max-concurrency",
            "5",
            "--async-no-reuse",
        ],
        Config(),
    )
    assert (
        args.async_mode
        and args.async_native
        and args.async_max_concurrency == 5
        and args.async_no_reuse
    )


def test_inbox_cli_options():
    args = burst_cli.parse_args(
        ["--imap-check", "h", "u", "p", "ALL", "--pop3-check", "p", "u2", "p2", "txt"],
        Config(),
    )
    assert args.imap_check == ["h", "u", "p", "ALL"]
    assert args.pop3_check == ["p", "u2", "p2", "txt"]


def test_logging_cli_flags():
    args = burst_cli.parse_args(["--silent"], Config())
    assert args.silent
    args = burst_cli.parse_args(["--errors-only"], Config())
    assert args.errors_only
    args = burst_cli.parse_args(["--warnings"], Config())
    assert args.warnings


def test_rdns_flag():
    args = burst_cli.parse_args(["--rdns-test"], Config())
    assert args.rdns_test


def test_outbound_test_flag():
    args = burst_cli.parse_args(["--outbound-test"], Config())
    assert args.outbound_test


def test_login_test_flag():
    args = burst_cli.parse_args(["--login-test"], Config())
    assert args.login_test


def test_auth_test_flag():
    args = burst_cli.parse_args(
        [
            "--auth-test",
            "--username",
            "u",
            "--password",
            "p",
        ],
        Config(),
    )
    assert args.auth_test and args.username == "u" and args.password == "p"


def test_template_and_enum_options(tmp_path):
    tpl = tmp_path / "tpl.txt"
    tpl.write_text("body")
    enum = tmp_path / "list.txt"
    enum.write_text("a\n")
    args = burst_cli.parse_args(
        [
            "--template-file",
            str(tpl),
            "--enum-list",
            str(enum),
            "--vrfy-enum",
            "--expn-enum",
            "--rcpt-enum",
        ],
        Config(),
    )
    assert args.template_file == str(tpl)
    assert args.enum_list == str(enum)
    assert args.vrfy_enum and args.expn_enum and args.rcpt_enum


def test_unknown_config_warning(tmp_path):
    cfg_path = tmp_path / "u.json"
    cfg_path.write_text(json.dumps({"bogus": 1}))
    with pytest.warns(RuntimeWarning):
        burst_cli.parse_args(["--config", str(cfg_path)], Config())


def test_new_message_mode_flags():
    args = burst_cli.parse_args(
        [
            "--unicode-case-test",
            "--utf7-test",
            "--header-tunnel-test",
            "--control-char-test",
        ],
        Config(),
    )
    assert args.unicode_case_test
    assert args.utf7_test
    assert args.header_tunnel_test
    assert args.control_char_test


def test_proxy_order_cli():
    args = burst_cli.parse_args(["--proxy-order", "random"], Config())
    assert args.proxy_order == "random"


def test_banner_check_flag():
    args = burst_cli.parse_args(["--banner-check"], Config())
    assert args.banner_check


def test_check_proxies_flag():
    args = burst_cli.parse_args(["--check-proxies"], Config())
    assert args.check_proxies


def test_auth_test_requires_credentials(caplog):
    args = burst_cli.parse_args(["--auth-test"], Config())
    assert args.auth_test and not args.username and not args.password

    with caplog.at_level(logging.ERROR, logger="smtpburst.__main__"):
        main_mod.main(["--auth-test"])

    assert any(
        "--auth-test requires --username and --password" in r.getMessage()
        for r in caplog.records
    )


def test_load_config_json(tmp_path):
    cfg = {"server": "json.test", "bursts": 1}
    path = tmp_path / "cfg.json"
    path.write_text(json.dumps(cfg))
    assert burst_cli.load_config(str(path)) == cfg


@pytest.mark.skipif(burst_cli.yaml is None, reason="PyYAML not installed")
def test_load_config_yaml(tmp_path):
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text("server: yaml.test\nbursts: 2\n")
    assert burst_cli.load_config(str(cfg_path)) == {"server": "yaml.test", "bursts": 2}


def test_parse_args_unknown_keys(tmp_path, monkeypatch):
    cfg_path = tmp_path / "unknown.json"
    cfg_path.write_text(json.dumps({"bogus": 1}))

    calls = []
    original = argparse.ArgumentParser.parse_args

    def track_parse_args(self, args=None, **kwargs):
        calls.append(args)
        return original(self, args, **kwargs)

    monkeypatch.setattr(argparse.ArgumentParser, "parse_args", track_parse_args)

    with pytest.warns(RuntimeWarning):
        burst_cli.parse_args(["--config", str(cfg_path)], Config())

    assert calls[0] == []
    assert calls[1] == ["--config", str(cfg_path)]


def test_parse_args_missing_config(tmp_path):
    cfg_path = tmp_path / "missing.json"
    with pytest.raises(SystemExit):
        burst_cli.parse_args(["--config", str(cfg_path)], Config())


def test_version_option(capsys):
    with pytest.raises(SystemExit):
        burst_cli.parse_args(["--version"], Config())
    out = capsys.readouterr().out
    assert out.strip() == __version__


def test_subcommand_shim_send():
    args = burst_cli.parse_args(["send", "--ssl"], Config())
    assert getattr(args, "cmd", None) == "send"
    assert args.ssl
