import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import burst_cli


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
