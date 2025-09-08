from __future__ import annotations

import imaplib
import poplib
from typing import List


def imap_search(
    host: str,
    user: str,
    password: str,
    *,
    criteria: str = "ALL",
    port: int = 993,
    ssl: bool = True,
    mailbox: str = "INBOX",
) -> List[bytes]:
    """Return message IDs matching ``criteria`` from IMAP server."""
    cls = imaplib.IMAP4_SSL if ssl else imaplib.IMAP4
    try:
        with cls(host, port) as imap:
            imap.login(user, password)
            imap.select(mailbox)
            typ, data = imap.search(None, criteria)
            if typ != "OK" or not data:
                return []
            return data[0].split()
    except (imaplib.IMAP4.error, OSError):
        return []


def pop3_search(
    host: str,
    user: str,
    password: str,
    *,
    pattern: bytes | None = None,
    port: int = 995,
    ssl: bool = True,
) -> List[int]:
    """Return message numbers containing ``pattern`` via POP3."""
    cls = poplib.POP3_SSL if ssl else poplib.POP3
    pop: poplib.POP3 | None = None
    try:
        pop = cls(host, port)
        pop.user(user)
        pop.pass_(password)
        ids: List[int] = []
        # ``stat`` provides the message count without fetching all IDs as
        # ``list`` would, making large mailboxes more efficient to scan.
        count, _ = pop.stat()
        for i in range(1, count + 1):
            resp, lines, _ = pop.retr(i)
            msg = b"\n".join(lines)
            if pattern is None or pattern in msg:
                ids.append(i)
        return ids
    except (poplib.error_proto, OSError):
        return []
    finally:
        if pop is not None:
            try:
                pop.quit()
            except Exception:
                pass
