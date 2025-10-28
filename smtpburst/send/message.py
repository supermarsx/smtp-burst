from __future__ import annotations

import mimetypes
from email.message import EmailMessage
from pathlib import Path
from typing import Optional

from ..config import Config
from .. import datagen
import logging

logger = logging.getLogger(__name__)


def append_message(cfg: Config, attachments: Optional[list[str]] = None) -> bytes:
    receivers = ", ".join(cfg.SB_RECEIVERS)
    body = cfg.SB_BODY
    if cfg.SB_TEST_CONTROL:
        body = "\x01\x02" + body
    if cfg.SB_TEMPLATE:
        body = cfg.SB_TEMPLATE.format(
            sender=cfg.SB_SENDER, receiver=receivers, subject=cfg.SB_SUBJECT
        )

    rand = datagen.generate(
        cfg.SB_SIZE,
        mode=cfg.SB_DATA_MODE,
        secure=cfg.SB_SECURE_RANDOM,
        words=cfg.SB_DICT_WORDS,
        repeat=cfg.SB_REPEAT_STRING,
        stream=cfg.SB_RAND_STREAM,
    )
    encoding = "utf-7" if cfg.SB_TEST_UTF7 else "utf-8"
    payload = body.encode(encoding) + b"\n\n" + rand

    msg = EmailMessage()
    if cfg.SB_TEST_UNICODE:
        msg["FrOm"] = cfg.SB_SENDER
        msg["tO"] = receivers
    else:
        msg["From"] = cfg.SB_SENDER
        msg["To"] = receivers
    msg["Subject"] = cfg.SB_SUBJECT
    if cfg.SB_TEST_TUNNEL:
        msg["X-Orig"] = "overlap"

    msg.set_content(payload, maintype="text", subtype="plain", cte="8bit")
    if cfg.SB_HTML_BODY:
        msg.add_alternative(cfg.SB_HTML_BODY, subtype="html")

    if cfg.SB_TRACE_ID:
        try:
            header_name = cfg.SB_TRACE_HEADER or "X-Burst-ID"
        except Exception:
            header_name = "X-Burst-ID"
        msg[header_name] = cfg.SB_TRACE_ID

    if cfg.SB_TEST_LONG_HEADERS:
        msg["X-Long-Header"] = "A" * 1000
    if cfg.SB_TEST_NESTED_MULTIPART:
        try:
            msg.make_mixed()
        except Exception:
            pass
        sub = EmailMessage()
        sub.set_content("nested text", subtype="plain")
        sub.add_alternative("<p>nested html</p>", subtype="html")
        msg.attach(sub)
    if cfg.SB_TEST_FILENAME_TRICK:
        tricky = "report\u202etxt.exe"
        msg.add_attachment(
            b"x", maintype="application", subtype="octet-stream", filename=tricky
        )

    if attachments:
        for path in attachments:
            try:
                data = Path(path).read_bytes()
            except (FileNotFoundError, OSError) as err:
                logger.warning("Skipping attachment %s: %s", path, err)
                continue
            ctype, _ = mimetypes.guess_type(path)
            if ctype:
                maintype, subtype = ctype.split("/", 1)
            else:
                maintype, subtype = "application", "octet-stream"
            msg.add_attachment(
                data, maintype=maintype, subtype=subtype, filename=Path(path).name
            )

    if cfg.SB_EICAR_TEST:
        eicar = b"X5O!P%@AP[4\nPZX54(P^)7CC)7}$EICAR-STD-ANTIVIRUS-TEST-FILE!$H+H*"
        msg.add_attachment(
            eicar, maintype="application", subtype="octet-stream", filename="eicar.com"
        )
    if getattr(cfg, "SB_SMIME_SAMPLE", False):
        smime = b"0\x82\x01\x0aPKCS7DUMMY"
        msg.add_attachment(
            smime, maintype="application", subtype="pkcs7-mime", filename="sample.p7m"
        )

    return msg.as_bytes()
