import sys
import time
from multiprocessing import Manager, Process

from smtpburst import config as cfg
from smtpburst import send
from smtpburst import cli


def main(argv=None):
    args = cli.parse_args(argv)

    if args.open_sockets:
        host, srv_port = send.parse_server(args.server)
        port = srv_port if ":" in args.server else args.port
        send.open_sockets(host, args.open_sockets, port)
        return

    cfg.SB_SERVER = args.server
    cfg.SB_SENDER = args.sender
    cfg.SB_RECEIVERS = args.receivers
    cfg.SB_SGEMAILS = args.emails_per_burst
    cfg.SB_BURSTS = args.bursts
    cfg.SB_SGEMAILSPSEC = args.email_delay
    cfg.SB_BURSTSPSEC = args.burst_delay
    cfg.SB_SIZE = args.size
    cfg.SB_STOPFAIL = args.stop_on_fail
    cfg.SB_STOPFQNT = args.stop_fail_count
    cfg.SB_TOTAL = cfg.SB_SGEMAILS * cfg.SB_BURSTS

    if args.proxy_file:
        with open(args.proxy_file, "r", encoding="utf-8") as fh:
            cfg.SB_PROXIES = [line.strip() for line in fh if line.strip()]
    if args.userlist:
        with open(args.userlist, "r", encoding="utf-8") as fh:
            cfg.SB_USERLIST = [line.strip() for line in fh if line.strip()]
    if args.passlist:
        with open(args.passlist, "r", encoding="utf-8") as fh:
            cfg.SB_PASSLIST = [line.strip() for line in fh if line.strip()]

    print("Starting smtp-burst")
    manager = Manager()
    SB_FAILCOUNT = manager.Value('i', 0)

    print(f"Generating {send.sizeof_fmt(cfg.SB_SIZE)} of data to append to message")
    SB_MESSAGE = send.appendMessage()
    print(f"Message using {send.sizeof_fmt(sys.getsizeof(SB_MESSAGE))} of random data")

    print(
        "Sending %s messages from %s to %s through %s"
        % (cfg.SB_TOTAL, cfg.SB_SENDER, cfg.SB_RECEIVERS, cfg.SB_SERVER)
    )

    for x in range(0, cfg.SB_BURSTS):
        quantity = range(1, cfg.SB_SGEMAILS + 1)
        procs = []

        if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
            break
        for number in quantity:
            if SB_FAILCOUNT.value >= cfg.SB_STOPFQNT and cfg.SB_STOPFAIL:
                break
            time.sleep(cfg.SB_SGEMAILSPSEC)
            proxy = None
            if cfg.SB_PROXIES:
                idx = (number + (x * cfg.SB_SGEMAILS) - 1) % len(cfg.SB_PROXIES)
                proxy = cfg.SB_PROXIES[idx]
            process = Process(
                target=send.sendmail,
                args=(
                    number + (x * cfg.SB_SGEMAILS),
                    x + 1,
                    SB_FAILCOUNT,
                    SB_MESSAGE,
                    cfg.SB_SERVER,
                    proxy,
                    cfg.SB_USERLIST,
                    cfg.SB_PASSLIST,
                ),
            )
            procs.append(process)
            process.start()

        for process in procs:
            process.join()
        time.sleep(cfg.SB_BURSTSPSEC)


if __name__ == "__main__":
    main()
