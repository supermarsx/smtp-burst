import time
import sys
import argparse
import socket
import signal
from multiprocessing import Process, Manager

from burstVars import *
from burstGen import *


def burst_sendmails():
    print("Starting smtp-burst")
    manager = Manager()
    SB_FAILCOUNT = manager.Value('i', 0)

    print("Generating %s of data to append to message" % (sizeof_fmt(SB_SIZE)))
    SB_MESSAGE = appendMessage()
    print("Message using %s of random data" % (sizeof_fmt(sys.getsizeof(SB_MESSAGE))))

    print("Sending %s messages from %s to %s through %s" % (SB_TOTAL, SB_SENDER, SB_RECEIVERS, SB_SERVER))

    for x in range(0, SB_BURSTS):
        quantity = range(1, SB_SGEMAILS + 1)
        procs = []

        if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL == True :
            break
        for index, number in enumerate(quantity):
            if SB_FAILCOUNT.value >= SB_STOPFQNT and SB_STOPFAIL == True :
                break
            time.sleep(SB_SGEMAILSPSEC)
            process = Process(target=sendmail, args=(number + (x * SB_SGEMAILS), x + 1, SB_FAILCOUNT, SB_MESSAGE))
            procs.append(process)
            process.start()

        for process in procs:
            process.join()
        time.sleep(SB_BURSTSPSEC)


def idle_socket_mode(duration):
    host = SB_SERVER
    port = 25
    if ':' in host:
        host, port_str = host.split(':', 1)
        port = int(port_str)

    sockets = []

    def cleanup(signum=None, frame=None):
        print("Closing %s sockets" % len(sockets))
        for s in sockets:
            try:
                s.close()
            except Exception:
                pass
        sockets.clear()

    signal.signal(signal.SIGINT, lambda s, f: (cleanup(), sys.exit(0)))
    signal.signal(signal.SIGTERM, lambda s, f: (cleanup(), sys.exit(0)))

    end = time.time() + duration
    while time.time() < end:
        try:
            s = socket.create_connection((host, port))
            sockets.append(s)
        except Exception as e:
            print("Socket error: %s" % e)
        time.sleep(0.1)

    cleanup()


def main():
    parser = argparse.ArgumentParser(description="smtp-burst")
    parser.add_argument('--idle-sockets', action='store_true', help='Open idle TCP sockets to the SMTP server')
    parser.add_argument('--duration', type=int, default=30, help='Duration to keep idle sockets open (seconds)')
    args = parser.parse_args()

    if args.idle_sockets:
        idle_socket_mode(args.duration)
    else:
        burst_sendmails()


if __name__ == '__main__':
    main()
