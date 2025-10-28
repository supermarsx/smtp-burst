from __future__ import annotations

from typing import Any

from . import discovery, attacks, inbox, send


def collect_results(args, cfg) -> dict[str, Any]:
    results: dict[str, Any] = {}
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
        from . import tlstest

        results["tls"] = tlstest.test_versions(host, port)
    if args.ssl_discovery:
        host, port = send.parse_server(args.ssl_discovery)
        from .discovery import ssl_probe

        results["ssl"] = ssl_probe.discover(host, port)
    if args.starttls_discovery:
        host, port = send.parse_server(args.starttls_discovery)
        from .discovery import starttls_probe

        results["starttls"] = starttls_probe.discover(host, port)
    if getattr(args, "starttls_details", None):
        host, port = send.parse_server(args.starttls_details)
        from .discovery import starttls_probe as _st

        results["starttls_details"] = _st.details(host, port)
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
    if args.rdns_test:
        host, _ = send.parse_server(args.server)
        from .discovery import rdns

        ok = rdns.verify(host)
        results["reverse_dns"] = "PASS" if ok else "FAIL"
    if args.banner_check:
        banner, ok = discovery.banner_check(args.server)
        results["banner"] = banner
        results["reverse_dns"] = "PASS" if ok else "FAIL"
    if args.esmtp_check:
        host, port = send.parse_server(args.esmtp_check)
        from .discovery import esmtp

        results["esmtp"] = esmtp.check(host, port)
    if args.mta_sts:
        from .discovery import mta

        results["mta_sts"] = mta.mta_sts_policy(args.mta_sts)
    if args.dane_tlsa:
        host, _ = send.parse_server(args.dane_tlsa)
        from .discovery import mta as _m

        results["dane_tlsa"] = _m.dane_tlsa(host)
    if args.blacklist_check:
        from .discovery import nettests

        results["blacklist"] = nettests.blacklist_check(
            args.blacklist_check[0], args.blacklist_check[1:]
        )
    if args.open_relay_test:
        from .discovery import nettests

        host, port = send.parse_server(args.server)
        results["open_relay"] = nettests.open_relay_test(host, port)
    if args.ping_test:
        from .discovery import nettests

        try:
            results["ping"] = nettests.ping(args.ping_test, timeout=args.ping_timeout)
        except nettests.CommandNotFoundError as exc:
            results["ping"] = str(exc)
    if args.traceroute_test:
        from .discovery import nettests

        try:
            results["traceroute"] = nettests.traceroute(
                args.traceroute_test, timeout=args.traceroute_timeout
            )
        except nettests.CommandNotFoundError as exc:
            results["traceroute"] = str(exc)
    if args.perf_test:
        host, port = send.parse_server(args.perf_test)
        results["performance"] = attacks.performance_test(
            host, port, baseline=args.baseline_host
        )
    if args.vrfy_enum or args.expn_enum or args.rcpt_enum:
        from .discovery import nettests

        host, port = send.parse_server(args.server)
        enum_items = cfg.SB_ENUM_LIST or cfg.SB_USERLIST
        if args.vrfy_enum:
            results["vrfy"] = nettests.vrfy_enum(host, enum_items, port=port)
        if args.expn_enum:
            results["expn"] = nettests.expn_enum(host, enum_items, port=port)
        if args.rcpt_enum:
            results["rcpt"] = nettests.rcpt_enum(host, enum_items, port=port)

    return results
