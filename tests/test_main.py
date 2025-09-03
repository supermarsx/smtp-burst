# Ensure project root is on sys.path for imports

from smtpburst import __main__ as main_mod
from smtpburst import send
from smtpburst import pipeline
import logging
import pytest


def test_main_open_sockets(monkeypatch):
    called = {}

    def fake_open(host, count, port, cfg=None, duration=None, iterations=None):
        called["args"] = (host, count, port, duration, iterations)

    monkeypatch.setattr(send, "open_sockets", fake_open)
    main_mod.main(
        [
            "--open-sockets",
            "2",
            "--server",
            "host.example:2525",
            "--socket-duration",
            "1",
            "--socket-iterations",
            "3",
        ]
    )
    assert called["args"] == ("host.example", 2, 2525, 1.0, 3)


def test_main_outbound_test(monkeypatch):
    calls = []

    def fake_send(cfg):
        calls.append("test")

    def fake_bomb(cfg):
        calls.append("bomb")

    monkeypatch.setattr(send, "send_test_email", fake_send)
    monkeypatch.setattr(send, "bombing_mode", fake_bomb)

    main_mod.main(["--outbound-test"])

    assert calls == ["test"]


def test_main_passes_attachments(monkeypatch, tmp_path):
    called = {}

    def fake_bomb(cfg, attachments=None):
        called["atts"] = attachments

    monkeypatch.setattr(send, "bombing_mode", fake_bomb)

    f = tmp_path / "a.txt"
    f.write_text("x")
    main_mod.main(["--attach", str(f)])

    assert called["atts"] == [str(f)]


def test_main_async_flag(monkeypatch):
    called = {}

    async def fake_async(cfg, attachments=None):
        called["mode"] = "async"

    def fake_sync(cfg, attachments=None):
        called["mode"] = "sync"

    monkeypatch.setattr(send, "async_bombing_mode", fake_async)
    monkeypatch.setattr(send, "bombing_mode", fake_sync)

    main_mod.main(["--async"])

    assert called["mode"] == "async"


def test_main_spawns_processes(monkeypatch):
    # Dummy Manager/Value implementation
    class DummyValue:
        def __init__(self, _type, value):
            self.value = value

    class DummyManager:
        def Value(self, typecode, value):
            return DummyValue(typecode, value)

    monkeypatch.setattr("multiprocessing.Manager", lambda: DummyManager())

    submitted = []

    class DummyPool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def submit(self, fn, *args, **kwargs):
            submitted.append(args)

            class DummyFuture:
                def result(self_inner):
                    return None

            return DummyFuture()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(send, "ProcessPoolExecutor", DummyPool)
    monkeypatch.setattr(send, "append_message", lambda cfg, attachments=None: b"msg")
    monkeypatch.setattr(send, "sizeof_fmt", lambda n: str(n))
    monkeypatch.setattr(send, "sendmail", lambda *a, **k: None)
    monkeypatch.setattr(send, "throttle", lambda cfg, delay=0.0: None)

    main_mod.main(["--emails-per-burst", "2", "--bursts", "3"])

    assert len(submitted) == 6


def test_logging_modes(monkeypatch, caplog):
    def dummy_bombing_mode(cfg, attachments=None):
        log = logging.getLogger("smtpburst.send")
        log.info("info")
        log.warning("warn")
        log.error("err")

    monkeypatch.setattr(send, "bombing_mode", dummy_bombing_mode)

    caplog.set_level(logging.INFO)
    main_mod.main([])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" in msgs and "warn" in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--warnings"])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" not in msgs and "warn" in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--errors-only"])
    msgs = [r.getMessage() for r in caplog.records]
    assert "info" not in msgs and "warn" not in msgs and "err" in msgs

    caplog.clear()
    main_mod.main(["--silent"])
    assert not caplog.records


def test_main_tls_discovery(monkeypatch):
    called = {}

    def fake_test(host, port):
        called["host"] = host
        called["port"] = port
        return {"TLSv1_2": {"supported": True}}

    def fake_report(res):
        called["report"] = res
        return "R"

    monkeypatch.setattr(main_mod.send, "parse_server", lambda s: ("h", 443))
    monkeypatch.setattr("smtpburst.tlstest.test_versions", fake_test)
    monkeypatch.setattr(main_mod, "ascii_report", fake_report)
    monkeypatch.setattr(main_mod.send, "bombing_mode", lambda cfg, attachments=None: None)

    main_mod.main(["--tls-discovery", "h"])

    assert called["host"] == "h"
    assert called["report"] == {"tls": {"TLSv1_2": {"supported": True}}}


def test_main_banner_check(monkeypatch):
    called = {}

    def fake_banner_check(server):
        called["server"] = server
        return ("banner", True)

    def fake_report(res):
        called["report"] = res
        return "formatted"

    monkeypatch.setattr(main_mod.discovery, "banner_check", fake_banner_check)
    monkeypatch.setattr(main_mod, "ascii_report", fake_report)
    monkeypatch.setattr(main_mod.send, "bombing_mode", lambda cfg, attachments=None: None)

    main_mod.main(["--banner-check", "--server", "srv"])

    assert called["server"] == "srv"
    assert called["report"] == {"banner": "banner", "reverse_dns": "PASS"}


def test_main_rdns_test(monkeypatch):
    called = {}

    def fake_verify(host):
        called["host"] = host
        return True

    def fake_report(res):
        called["report"] = res
        return "formatted"

    monkeypatch.setattr(main_mod.discovery.rdns, "verify", fake_verify)
    monkeypatch.setattr(main_mod, "ascii_report", fake_report)
    monkeypatch.setattr(main_mod.send, "bombing_mode", lambda cfg, attachments=None: None)

    main_mod.main(["--rdns-test", "--server", "host"])

    assert called["host"] == "host"
    assert called["report"] == {"reverse_dns": "PASS"}


def test_main_ping_timeout(monkeypatch):
    called = {}

    def fake_bomb(cfg, attachments=None):
        pass

    def fake_ping(host, count=1, timeout=1):
        called["host"] = host
        called["timeout"] = timeout
        return "ok"

    monkeypatch.setattr(main_mod.send, "bombing_mode", fake_bomb)
    monkeypatch.setattr(main_mod.nettests, "ping", fake_ping)

    main_mod.main(["--ping-test", "host", "--ping-timeout", "7"])

    assert called == {"host": "host", "timeout": 7}


def test_main_traceroute_timeout(monkeypatch):
    called = {}

    def fake_bomb(cfg, attachments=None):
        pass

    def fake_traceroute(host, count=30, timeout=5):
        called["host"] = host
        called["timeout"] = timeout
        return "ok"

    monkeypatch.setattr(main_mod.send, "bombing_mode", fake_bomb)
    monkeypatch.setattr(main_mod.nettests, "traceroute", fake_traceroute)

    main_mod.main(["--traceroute-test", "host", "--traceroute-timeout", "9"])

    assert called == {"host": "host", "timeout": 9}


def test_main_pipeline_error(monkeypatch, capsys):
    def fake_load(path):
        raise pipeline.PipelineError("bad pipeline")

    monkeypatch.setattr(pipeline, "load_pipeline", fake_load)

    main_mod.main(["--pipeline-file", "p.yml"])

    out = capsys.readouterr().out
    assert "bad pipeline" in out


def test_report_file(monkeypatch, tmp_path):
    def fake_bomb(cfg, attachments=None):
        pass

    def fake_ping(host, count=1, timeout=1):
        return "pong"

    monkeypatch.setattr(main_mod.send, "bombing_mode", fake_bomb)
    monkeypatch.setattr(main_mod.nettests, "ping", fake_ping)

    out_file = tmp_path / "report.txt"
    main_mod.main(["--ping-test", "host", "--report-file", str(out_file)])

    expected = main_mod.ascii_report({"ping": "pong"})
    assert out_file.read_text() == expected


def test_main_exits_on_error(monkeypatch):
    def bad_bomb(cfg, attachments=None):
        raise ValueError("bad mode")

    monkeypatch.setattr(send, "bombing_mode", bad_bomb)

    with pytest.raises(SystemExit) as excinfo:
        main_mod.main([])

    assert excinfo.value.code == 1
