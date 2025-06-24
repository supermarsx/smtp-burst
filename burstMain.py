import time
import sys
from multiprocessing import Process, Manager

import burstVars
import burstGen
import burst_cli

# Main script routine
if __name__ == '__main__':
    args = burst_cli.parse_args()

    burstVars.SB_SERVER = args.server
    burstVars.SB_SENDER = args.sender
    burstVars.SB_RECEIVERS = args.receivers
    burstVars.SB_SGEMAILS = args.emails_per_burst
    burstVars.SB_BURSTS = args.bursts
    burstVars.SB_SGEMAILSPSEC = args.email_delay
    burstVars.SB_BURSTSPSEC = args.burst_delay
    burstVars.SB_SIZE = args.size
    burstVars.SB_STOPFAIL = args.stop_on_fail
    burstVars.SB_STOPFQNT = args.stop_fail_count
    burstVars.SB_TOTAL = burstVars.SB_SGEMAILS * burstVars.SB_BURSTS

    burstGen.SB_SERVER = burstVars.SB_SERVER
    burstGen.SB_SENDER = burstVars.SB_SENDER
    burstGen.SB_RECEIVERS = burstVars.SB_RECEIVERS
    burstGen.SB_SGEMAILS = burstVars.SB_SGEMAILS
    burstGen.SB_BURSTS = burstVars.SB_BURSTS
    burstGen.SB_SGEMAILSPSEC = burstVars.SB_SGEMAILSPSEC
    burstGen.SB_BURSTSPSEC = burstVars.SB_BURSTSPSEC
    burstGen.SB_SIZE = burstVars.SB_SIZE
    burstGen.SB_STOPFAIL = burstVars.SB_STOPFAIL
    burstGen.SB_STOPFQNT = burstVars.SB_STOPFQNT
    burstGen.SB_TOTAL = burstVars.SB_TOTAL
    if args.proxy_list:
        with open(args.proxy_list) as f:
            burstVars.SB_PROXIES = [line.strip() for line in f if line.strip()]
    burstGen.SB_PROXIES = burstVars.SB_PROXIES
    burstVars.SB_ROTATE_PROXIES = args.rotate_proxies
    burstGen.SB_ROTATE_PROXIES = burstVars.SB_ROTATE_PROXIES

    print("Starting smtp-burst")
    manager = Manager()
    SB_FAILCOUNT = manager.Value('i', 0)

    print("Generating %s of data to append to message" % (burstGen.sizeof_fmt(burstVars.SB_SIZE)))
    SB_MESSAGE = burstGen.appendMessage()
    print("Message using %s of random data" % (burstGen.sizeof_fmt(sys.getsizeof(SB_MESSAGE))))

    print(
        "Sending %s messages from %s to %s through %s"
        % (burstVars.SB_TOTAL, burstVars.SB_SENDER, burstVars.SB_RECEIVERS, burstVars.SB_SERVER)
    )

    for x in range(0, burstVars.SB_BURSTS):
        quantity = range(1, burstVars.SB_SGEMAILS + 1)
        procs = []

        if SB_FAILCOUNT.value >= burstVars.SB_STOPFQNT and burstVars.SB_STOPFAIL:
            break
        for index, number in enumerate(quantity):
            if SB_FAILCOUNT.value >= burstVars.SB_STOPFQNT and burstVars.SB_STOPFAIL:
                break
            time.sleep(burstVars.SB_SGEMAILSPSEC)
            process = Process(
                target=burstGen.sendmail,
                args=(number + (x * burstVars.SB_SGEMAILS), x + 1, SB_FAILCOUNT, SB_MESSAGE),
            )
            procs.append(process)
            process.start()

        for process in procs:
            process.join()
        time.sleep(burstVars.SB_BURSTSPSEC)
