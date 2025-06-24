import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from smtpburst import cli as burst_cli


def test_json_config_parsing(tmp_path):
    cfg = {"server": "json.example.com", "bursts": 2}
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps(cfg))

    args = burst_cli.parse_args(["--config", str(cfg_path)])
    assert args.server == "json.example.com"
    assert args.bursts == 2


def test_cli_overrides_config(tmp_path):
    cfg = {"server": "should.be.overridden"}
    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps(cfg))

    args = burst_cli.parse_args(["--config", str(cfg_path), "--server", "cli.example.com"])
    assert args.server == "cli.example.com"


def test_yaml_config_parsing(tmp_path):
    yaml_cfg = "server: yaml.example.com\n"
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml_cfg)

    args = burst_cli.parse_args(["--config", str(cfg_path)])
    assert args.server == "yaml.example.com"


def test_open_sockets_option():
    args = burst_cli.parse_args(["--open-sockets", "5"])
    assert args.open_sockets == 5


def test_proxy_file_option(tmp_path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("127.0.0.1:1080\n")
    args = burst_cli.parse_args(["--proxy-file", str(proxy_file)])
    assert args.proxy_file == str(proxy_file)


def test_ssl_flag():
    args = burst_cli.parse_args(["--ssl"])
    assert args.ssl


def test_starttls_flag():
    args = burst_cli.parse_args(["--starttls"])
    assert args.starttls


def test_subject_option():
    args = burst_cli.parse_args(["--subject", "MySub"])
    assert args.subject == "MySub"


def test_body_file_option(tmp_path):
    body_file = tmp_path / "body.txt"
    body_file.write_text("hello")
    args = burst_cli.parse_args(["--body-file", str(body_file)])
    assert args.body_file == str(body_file)
