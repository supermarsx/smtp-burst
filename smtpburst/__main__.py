import logging
from pathlib import Path

from smtpburst.config import Config
from smtpburst import send
from smtpburst import cli
from smtpburst import discovery
from smtpburst.discovery import nettests
from smtpburst.reporting import ascii_report
from smtpburst import inbox
from smtpburst import attacks
from smtpburst.datagen import load_wordlist

logger = logging.getLogger(__name__)


def main(argv=None):
    cfg = Config()
    args = cli.parse_args(argv, cfg)

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
        )
    cfg.SB_PROXY_ORDER = args.proxy_order
    cfg.SB_CHECK_PROXIES = args.check_proxies
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
            logger.info(ascii_report(res))
        return

    if args.auth_test:
        logger.info("Running SMTP auth method test")
        if not cfg.SB_USERNAME or not cfg.SB_PASSWORD:
            logger.error("--auth-test requires --username and --password")
            return
        res = send.auth_test(cfg)
        if res:
            logger.info(ascii_report(res))
        return

    logger.info("Starting smtp-burst")
    send.bombing_mode(cfg, attachments=args.attach)

    results = {}
    if args.check_dmarc:
        results["dmarc"] = discovery.check_dmarc(args.check_dmarc)
    if args.check_spf:
        results["spf"] = discovery.check_spf(args.check_spf)
    if args.check_dkim:
        results["dkim"] = discovery.check_dkim(args.check_dkim)
    if args.check_srv:
        results["srv"] = discovery.check_srv(args.check_srv)
    if args.check_soa:
        results["soa"] = discovery.check_soa(args.check_soa)
    if args.check_txt:
        results["txt"] = discovery.check_txt(args.check_txt)
    if args.lookup_mx:
        results["mx"] = discovery.lookup_mx(args.lookup_mx)
    if args.smtp_extensions:
        host, port = send.parse_server(args.smtp_extensions)
        results["smtp_extensions"] = discovery.smtp_extensions(host, port)
    if args.cert_check:
        host, port = send.parse_server(args.cert_check)
        results["certificate"] = discovery.check_certificate(host, port)
    if args.port_scan:
        host = args.port_scan[0]
        ports = [int(p) for p in args.port_scan[1:]]
        results["port_scan"] = discovery.port_scan(host, ports)
    if args.probe_honeypot:
        host, port = send.parse_server(args.probe_honeypot)
        results["honeypot"] = discovery.probe_honeypot(host, port)
    if args.tls_discovery:
        host, port = send.parse_server(args.tls_discovery)
        from smtpburst import tlstest

        results["tls"] = tlstest.test_versions(host, port)
    if args.ssl_discovery:
        host, port = send.parse_server(args.ssl_discovery)
        from smtpburst.discovery import ssl_probe

        results["ssl"] = ssl_probe.discover(host, port)
    if args.imap_check:
        host, user, pwd, crit = args.imap_check
        host, port = send.parse_server(host)
        results["imap"] = inbox.imap_search(host, user, pwd, criteria=crit, port=port)
    if args.pop3_check:
        host, user, pwd, patt = args.pop3_check
        host, port = send.parse_server(host)
        results["pop3"] = inbox.pop3_search(
            host, user, pwd, pattern=patt.encode(), port=port
        )
    if args.blacklist_check:
        results["blacklist"] = nettests.blacklist_check(
            args.blacklist_check[0], args.blacklist_check[1:]
        )
    if args.open_relay_test:
        host, port = send.parse_server(args.server)
        results["open_relay"] = nettests.open_relay_test(host, port)
    if args.ping_test:
        results["ping"] = nettests.ping(args.ping_test)
    if args.traceroute_test:
        results["traceroute"] = nettests.traceroute(args.traceroute_test)
    if args.perf_test:
        host, port = send.parse_server(args.perf_test)
        results["performance"] = attacks.performance_test(
            host, port, baseline=args.baseline_host
        )
    if args.vrfy_enum or args.expn_enum or args.rcpt_enum:
        host, port = send.parse_server(args.server)
        enum_items = cfg.SB_ENUM_LIST or cfg.SB_USERLIST
        if args.vrfy_enum:
            results["vrfy"] = nettests.vrfy_enum(host, enum_items, port=port)
        if args.expn_enum:
            results["expn"] = nettests.expn_enum(host, enum_items, port=port)
        if args.rcpt_enum:
            results["rcpt"] = nettests.rcpt_enum(host, enum_items, port=port)
    if args.rdns_test:
        host, _ = send.parse_server(args.server)
        from smtpburst import rdns

        ok = rdns.verify(host)
        msg = "Reverse DNS: PASS" if ok else "Reverse DNS: FAIL"
        print(msg)
    if args.banner_check:
        banner, ok = discovery.banner_check(args.server)
        print(f"Banner: {banner}")
        msg = "Reverse DNS: PASS" if ok else "Reverse DNS: FAIL"
        print(msg)
    if results:
        logger.info(ascii_report(results))


if __name__ == "__main__":
    main()
