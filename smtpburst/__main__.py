import sys
import logging

from smtpburst.config import Config
from smtpburst import send
from smtpburst import cli
from smtpburst import discovery, nettests
from smtpburst import report

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

    if args.open_sockets:
        host, srv_port = send.parse_server(args.server)
        port = srv_port if ":" in args.server else args.port
        send.open_sockets(host, args.open_sockets, port)
        return

    cfg.SB_SERVER = args.server
    cfg.SB_SENDER = args.sender
    cfg.SB_RECEIVERS = args.receivers
    cfg.SB_SUBJECT = args.subject
    cfg.SB_SGEMAILS = args.emails_per_burst
    cfg.SB_BURSTS = args.bursts
    cfg.SB_SGEMAILSPSEC = args.email_delay
    cfg.SB_BURSTSPSEC = args.burst_delay
    cfg.SB_SIZE = args.size
    cfg.SB_DATA_MODE = args.data_mode
    cfg.SB_REPEAT_STRING = args.repeat_string
    cfg.SB_PER_BURST_DATA = args.per_burst_data
    cfg.SB_SECURE_RANDOM = args.secure_random
    cfg.SB_STOPFAIL = args.stop_on_fail
    cfg.SB_STOPFQNT = args.stop_fail_count
    cfg.SB_SSL = args.ssl
    cfg.SB_STARTTLS = args.starttls

    if args.dict_file:
        cfg.SB_DICT_WORDS = send.datagen.compile_wordlist(args.dict_file)
    if args.rand_stream:
        cfg.SB_RAND_STREAM = open(args.rand_stream, "rb")

    if args.proxy_file:
        with open(args.proxy_file, "r", encoding="utf-8") as fh:
            cfg.SB_PROXIES = [line.strip() for line in fh if line.strip()]
    if args.userlist:
        with open(args.userlist, "r", encoding="utf-8") as fh:
            cfg.SB_USERLIST = [line.strip() for line in fh if line.strip()]
    if args.passlist:
        with open(args.passlist, "r", encoding="utf-8") as fh:
            cfg.SB_PASSLIST = [line.strip() for line in fh if line.strip()]
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as fh:
            cfg.SB_BODY = fh.read()

    logger.info("Starting smtp-burst")
    send.bombing_mode(cfg)

    results = {}
    if args.check_dmarc:
        results['dmarc'] = discovery.check_dmarc(args.check_dmarc)
    if args.check_spf:
        results['spf'] = discovery.check_spf(args.check_spf)
    if args.check_dkim:
        results['dkim'] = discovery.check_dkim(args.check_dkim)
    if args.check_srv:
        results['srv'] = discovery.check_srv(args.check_srv)
    if args.check_soa:
        results['soa'] = discovery.check_soa(args.check_soa)
    if args.check_txt:
        results['txt'] = discovery.check_txt(args.check_txt)
    if args.blacklist_check:
        results['blacklist'] = nettests.blacklist_check(
            args.blacklist_check[0], args.blacklist_check[1:]
        )
    if args.open_relay_test:
        host, port = send.parse_server(args.server)
        results['open_relay'] = nettests.open_relay_test(host, port)
    if args.ping_test:
        results['ping'] = nettests.ping(args.ping_test)
    if args.traceroute_test:
        results['traceroute'] = nettests.traceroute(args.traceroute_test)
    if results:
        logger.info(report.ascii_report(results))


if __name__ == "__main__":
    main()
