import argparse
import burstVars


def build_parser():
    """Return argument parser for smtp-burst."""
    parser = argparse.ArgumentParser(
        description="Send bursts of SMTP emails for testing purposes"    )
    parser.add_argument(
        "--server",
        default=burstVars.SB_SERVER,
        help="SMTP server to connect to",
    )
    parser.add_argument(
        "--sender",
        default=burstVars.SB_SENDER,
        help="Envelope sender address",
    )
    parser.add_argument(
        "--receivers",
        nargs="+",
        default=burstVars.SB_RECEIVERS,
        help="Space separated list of recipient addresses",
    )
    parser.add_argument(
        "--emails-per-burst",
        type=int,
        default=burstVars.SB_SGEMAILS,
        help="Number of emails per burst",
    )
    parser.add_argument(
        "--bursts",
        type=int,
        default=burstVars.SB_BURSTS,
        help="Number of bursts to send",
    )
    parser.add_argument(
        "--email-delay",
        type=float,
        default=burstVars.SB_SGEMAILSPSEC,
        help="Delay in seconds between individual emails",
    )
    parser.add_argument(
        "--burst-delay",
        type=float,
        default=burstVars.SB_BURSTSPSEC,
        help="Delay in seconds between bursts",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=burstVars.SB_SIZE,
        help="Random data size in bytes appended to each message",
    )
    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        default=burstVars.SB_STOPFAIL,
        help="Stop execution when --stop-fail-count failures occur",
    )
    parser.add_argument(
        "--stop-fail-count",
        type=int,
        default=burstVars.SB_STOPFQNT,
        help="Number of failed emails that triggers stopping",
    )
    return parser


def parse_args(args=None):
    """Parse command line arguments."""
    parser = build_parser()
    return parser.parse_args(args)

