import sys
import time
from multiprocessing import Manager, Process

from smtpburst import send
from smtpburst import cli
from smtpburst.config import Config


def main(argv=None):
    cfg = Config()
    args = cli.parse_args(argv, cfg)

    if args.open_sockets:
        host, srv_port = send.parse_server(args.server)
        port = srv_port if ":" in args.server else args.port
        send.open_sockets(host, args.open_sockets, port)
        return

    cfg.server = args.server
    cfg.sender = args.sender
    cfg.receivers = args.receivers
    cfg.subject = args.subject
    cfg.emails_per_burst = args.emails_per_burst
    cfg.bursts = args.bursts
    cfg.email_delay = args.email_delay
    cfg.burst_delay = args.burst_delay
    cfg.size = args.size
    cfg.stop_on_fail = args.stop_on_fail
    cfg.stop_fail_count = args.stop_fail_count
    cfg.ssl = args.ssl
    cfg.starttls = args.starttls

    if args.proxy_file:
        with open(args.proxy_file, "r", encoding="utf-8") as fh:
            cfg.proxies = [line.strip() for line in fh if line.strip()]
    if args.userlist:
        with open(args.userlist, "r", encoding="utf-8") as fh:
            cfg.userlist = [line.strip() for line in fh if line.strip()]
    if args.passlist:
        with open(args.passlist, "r", encoding="utf-8") as fh:
            cfg.passlist = [line.strip() for line in fh if line.strip()]
    if args.body_file:
        with open(args.body_file, "r", encoding="utf-8") as fh:
            cfg.body = fh.read()

    print("Starting smtp-burst")
    manager = Manager()
    SB_FAILCOUNT = manager.Value('i', 0)

    print(f"Generating {send.sizeof_fmt(cfg.size)} of data to append to message")
    SB_MESSAGE = send.appendMessage(cfg)
    print(f"Message using {send.sizeof_fmt(sys.getsizeof(SB_MESSAGE))} of random data")

    print(
        "Sending %s messages from %s to %s through %s"
        % (cfg.total, cfg.sender, cfg.receivers, cfg.server)
    )

    for x in range(0, cfg.bursts):
        quantity = range(1, cfg.emails_per_burst + 1)
        procs = []

        if SB_FAILCOUNT.value >= cfg.stop_fail_count and cfg.stop_on_fail:
            break
        for number in quantity:
            if SB_FAILCOUNT.value >= cfg.stop_fail_count and cfg.stop_on_fail:
                break
            time.sleep(cfg.email_delay)
            proxy = None
            if cfg.proxies:
                idx = (number + (x * cfg.emails_per_burst) - 1) % len(cfg.proxies)
                proxy = cfg.proxies[idx]
            process = Process(
                target=send.sendmail,
                args=(
                    number + (x * cfg.emails_per_burst),
                    x + 1,
                    SB_FAILCOUNT,
                    SB_MESSAGE,
                    cfg,
                    proxy,
                ),
            )
            procs.append(process)
            process.start()

        for process in procs:
            process.join()
        time.sleep(cfg.burst_delay)


if __name__ == "__main__":
    main()
