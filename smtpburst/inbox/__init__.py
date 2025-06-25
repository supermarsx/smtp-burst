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
    with cls(host, port) as imap:
        imap.login(user, password)
        imap.select(mailbox)
        typ, data = imap.search(None, criteria)
        if typ != "OK" or not data:
            return []
        return data[0].split()


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
    pop = cls(host, port)
    try:
        pop.user(user)
        pop.pass_(password)
        ids: List[int] = []
        count = len(pop.list()[1])
        for i in range(1, count + 1):
            resp, lines, _ = pop.retr(i)
            msg = b"\n".join(lines)
            if pattern is None or pattern in msg:
                ids.append(i)
        return ids
    finally:
        try:
            pop.quit()
        except Exception:
            pass
