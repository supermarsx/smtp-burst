import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from smtpburst import pipeline


def test_cli_pipeline_option():
    from smtpburst import cli
    from smtpburst.config import Config

    args = cli.parse_args(["--pipeline-file", "p.yml"], Config())
    assert args.pipeline_file == "p.yml"


def test_load_pipeline_missing_yaml(monkeypatch):
    monkeypatch.setattr(pipeline, "yaml", None)
    with pytest.raises(SystemExit, match="PyYAML"):
        pipeline.load_pipeline("p.yml")


@pytest.mark.skipif(pipeline.yaml is None, reason="PyYAML not installed")
def test_pipeline_runner_stop(monkeypatch, tmp_path):
    calls = []

    def ok():
        calls.append("ok")
        return True

    def bad():
        calls.append("bad")
        return False

    monkeypatch.setitem(pipeline.ACTION_MAP, "ok", lambda: ok())
    monkeypatch.setitem(pipeline.ACTION_MAP, "bad", lambda: bad())

    cfg = {
        "steps": [
            {"action": "ok"},
            {"action": "bad"},
            {"action": "ok"},
        ],
        "stop_on_fail": True,
        "fail_threshold": 1,
    }

    path = tmp_path / "p.yaml"
    import yaml

    path.write_text(yaml.safe_dump(cfg))

    runner = pipeline.load_pipeline(str(path))
    res = runner.run()
    assert calls == ["ok", "bad"]
    assert len(res) == 2


@pytest.mark.skipif(pipeline.yaml is None, reason="PyYAML not installed")
def test_load_pipeline_missing_steps(tmp_path):
    import yaml
    cfg = {"stop_on_fail": True}
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(pipeline.PipelineError):
        pipeline.load_pipeline(str(path))


@pytest.mark.skipif(pipeline.yaml is None, reason="PyYAML not installed")
def test_load_pipeline_steps_not_list(tmp_path):
    import yaml
    cfg = {"steps": {"action": "ok"}}
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(pipeline.PipelineError):
        pipeline.load_pipeline(str(path))


def test_pipeline_runner_invalid_actions():
    runner = pipeline.PipelineRunner([{}])
    with pytest.raises(pipeline.PipelineError):
        runner.run()
    runner = pipeline.PipelineRunner([{"action": "nope"}])
    with pytest.raises(pipeline.PipelineError):
        runner.run()


@pytest.mark.skipif(pipeline.yaml is None, reason="PyYAML not installed")
def test_pipeline_runner_stop_threshold(monkeypatch, tmp_path):
    calls = []

    def bad():
        calls.append("bad")
        return False

    def ok():
        calls.append("ok")
        return True

    monkeypatch.setitem(pipeline.ACTION_MAP, "bad", lambda: bad())
    monkeypatch.setitem(pipeline.ACTION_MAP, "ok", lambda: ok())

    cfg = {
        "steps": [
            {"action": "bad"},
            {"action": "bad"},
            {"action": "ok"},
        ],
        "stop_on_fail": True,
        "fail_threshold": 2,
    }

    import yaml
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(cfg))

    runner = pipeline.load_pipeline(str(path))
    res = runner.run()
    assert calls == ["bad", "bad"]
    assert len(res) == 2


@pytest.mark.skipif(pipeline.yaml is None, reason="PyYAML not installed")
def test_pipeline_step_not_mapping(tmp_path):
    import yaml

    cfg = {"steps": ["oops"]}
    path = tmp_path / "p.yaml"
    path.write_text(yaml.safe_dump(cfg))

    runner = pipeline.load_pipeline(str(path))
    with pytest.raises(pipeline.PipelineError, match="mapping"):
        runner.run()
