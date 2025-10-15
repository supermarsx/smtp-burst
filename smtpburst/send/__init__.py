from __future__ import annotations

import smtplib  # re-exported for tests (monkeypatching)
from concurrent.futures import ProcessPoolExecutor  # for tests monkeypatching
from .. import attacks  # re-export attacks module for tests
import socket  # re-export for tests
import time  # re-export for tests
from smtplib import SMTPException  # convenient alias used in tests

# Core helpers
from .core import (
    throttle,
    async_throttle,
    append_message,
    sizeof_fmt,
    _async_increment,
    _increment,
    sendmail,
    async_sendmail,
    parse_server,
)
from .utils import open_sockets

# Auth helpers
from .auth import _attempt_auth, _smtp_authenticate, login_test, auth_test

# Sending modes
from .modes import (
    send_test_email,
    bombing_mode,
    async_bombing_mode,
)
from .native import _async_sendmail_native, _async_bombing_mode_native

__all__ = [
    # stdlib re-exports expected by tests
    "smtplib",
    "attacks",
    "socket",
    "time",
    "ProcessPoolExecutor",
    "SMTPException",
    # core
    "throttle",
    "async_throttle",
    "append_message",
    "sizeof_fmt",
    "_async_increment",
    "_increment",
    "sendmail",
    "async_sendmail",
    "parse_server",
    "open_sockets",
    # auth
    "_attempt_auth",
    "_smtp_authenticate",
    "login_test",
    "auth_test",
    # modes
    "send_test_email",
    "bombing_mode",
    "async_bombing_mode",
    "_async_sendmail_native",
    "_async_bombing_mode_native",
]
