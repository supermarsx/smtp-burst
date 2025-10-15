import logging
from pathlib import Path
import asyncio

from smtpburst.config import Config
from smtpburst import send
from smtpburst import cli
from smtpburst.reporting import ascii_report, json_report, yaml_report, junit_report
# Imported for tests to monkeypatch on main module
from smtpburst import discovery  # noqa: F401
from smtpburst.discovery import nettests  # noqa: F401
from smtpburst.datagen import load_wordlist
from smtpburst.main_helpers import collect_results

logger = logging.getLogger(__name__)


def main(argv=None):
    cfg = Config()
    args = cli.parse_args(argv, cfg)

    reporters = {
        "ascii": ascii_report,
        "json": json_report,
        "yaml": yaml_report,
        "junit": junit_report,
    }
    report = reporters.get(args.report_format, ascii_report)

    if args.silent:
        level = logging.CRITICAL
    elif args.errors_only:
        level = logging.ERROR
    elif args.warnings:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s:%(message)s")
    logging.getLogger().setLevel(level)

    # Optional subcommand guidance (non-breaking)
    cmd = getattr(args, "cmd", None)
    if cmd == "suite" and not args.pipeline_file:
        print("suite subcommand requires --pipeline-file")
        return
    if cmd == "inbox" and not (args.imap_check or args.pop3_check):
        print("inbox subcommand expects --imap-check or --pop3-check")
        return
    if cmd == "auth" and not (args.login_test or args.auth_test):
        print("auth subcommand expects --login-test or --auth-test")
        return
    if cmd == "discovery":
        discovery_flags = (
            args.check_dmarc
            or args.check_spf
            or args.check_dkim
            or args.check_srv
            or args.check_soa
            or args.check_txt
            or args.lookup_mx
            or args.smtp_extensions
            or args.cert_check
            or args.port_scan
            or args.probe_honeypot
            or args.tls_discovery
            or args.ssl_discovery
            or args.starttls_discovery
            or args.esmtp_check
            or args.banner_check
            or args.rdns_test
        )
        if not discovery_flags:
            print(
                "discovery subcommand expects one or more discovery flags (see --help)"
            )
            return

    if args.pipeline_file:
        from . import pipeline

        try:
            runner = pipeline.load_pipeline(args.pipeline_file)
        except (SystemExit, pipeline.PipelineError) as exc:
            print(exc)
            return
        runner.run()
        return

    if args.open_sockets:
        host, srv_port = send.parse_server(args.server)
        port = srv_port if ":" in args.server else args.port
        send.open_sockets(
            host,
            args.open_sockets,
            port,
            cfg,
            duration=args.socket_duration,
            iterations=args.socket_iterations,
        )
        return

    cli.apply_args_to_config(cfg, args)

    if args.dict_file:
        cfg.SB_DICT_WORDS = send.datagen.compile_wordlist(Path(args.dict_file))
    if args.rand_stream:
        cfg.SB_RAND_STREAM = Path(args.rand_stream).open("rb")

    if args.proxy_file:
        from . import proxy

        cfg.SB_PROXIES = proxy.load_proxies(
            Path(args.proxy_file),
            order=args.proxy_order,
            check=args.check_proxies,
            timeout=args.proxy_timeout,
        )
    cfg.SB_PROXY_ORDER = args.proxy_order
    cfg.SB_CHECK_PROXIES = args.check_proxies
    cfg.SB_PROXY_TIMEOUT = args.proxy_timeout
    if args.userlist:
        cfg.SB_USERLIST = load_wordlist(Path(args.userlist))
    if args.passlist:
        cfg.SB_PASSLIST = load_wordlist(Path(args.passlist))
    if args.username:
        cfg.SB_USERNAME = args.username
    if args.password:
        cfg.SB_PASSWORD = args.password
    if args.body_file:
        cfg.SB_BODY = Path(args.body_file).read_text(encoding="utf-8")
    if args.html_body_file:
        cfg.SB_HTML_BODY = Path(args.html_body_file).read_text(encoding="utf-8")
    if args.template_file:
        cfg.SB_TEMPLATE = Path(args.template_file).read_text(encoding="utf-8")
    if args.enum_list:
        cfg.SB_ENUM_LIST = load_wordlist(Path(args.enum_list))

    if args.outbound_test:
        logger.info("Sending outbound test message")
        send.send_test_email(cfg)
        return

    if args.login_test:
        logger.info("Running SMTP login test")
        res = send.login_test(cfg)
        if res:
            logger.info(report(res))
        return

    if args.auth_test:
        logger.info("Running SMTP auth method test")
        if not cfg.SB_USERNAME or not cfg.SB_PASSWORD:
            logger.error("--auth-test requires --username and --password")
            return
        res = send.auth_test(cfg)
        if res:
            logger.info(report(res))
        return
    if getattr(args, "auth_matrix", None):
        logger.info("Building AUTH matrix")
        host, port = send.parse_server(args.auth_matrix)
        if not args.username or not args.password:
            logger.error("--auth-matrix requires --username and --password")
            return
        # Build config and run auth_test against advertised mechs
        mcfg = Config()
        mcfg.SB_SERVER = f"{host}:{port}"
        mcfg.SB_USERNAME = args.username
        mcfg.SB_PASSWORD = args.password
        base = send.auth_test(mcfg)
        # Fill missing mechanisms as False if --auth-mechs provided
        mechs = getattr(args, "auth_mechs", None)
        if mechs:
            matrix = {m: bool(base.get(m)) for m in mechs}
        else:
            matrix = base
        results = {"auth_matrix": matrix}
        formatted = report(results)
        logger.info(formatted)
        if args.report_file:
            Path(args.report_file).write_text(formatted, encoding="utf-8")
        return

    logger.info("Starting smtp-burst")
    try:
        if args.async_mode:
            asyncio.run(send.async_bombing_mode(cfg, attachments=args.attach))
        else:
            send.bombing_mode(cfg, attachments=args.attach)
    except ValueError as exc:
        logger.error(exc)
        raise SystemExit(1) from exc

    results = collect_results(args, cfg)
    if results:
        formatted = report(results)
        logger.info(formatted)
        if args.report_file:
            Path(args.report_file).write_text(formatted, encoding="utf-8")


if __name__ == "__main__":
    main()
