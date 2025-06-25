from dataclasses import dataclass, field
from typing import List, Optional, TextIO

# Size constants
SZ_KILOBYTE = 1024
SZ_MEGABYTE = 1024 * SZ_KILOBYTE
SZ_GIGABYTE = 1024 * SZ_MEGABYTE
SZ_TERABYTE = 1024 * SZ_GIGABYTE


@dataclass
class Config:
    """Runtime configuration options."""

    SB_SGEMAILS: int = 5
    SB_SGEMAILSPSEC: float = 1
    SB_BURSTS: int = 3
    SB_BURSTSPSEC: float = 3
    SB_SIZE: int = 5 * SZ_MEGABYTE * 2
    SB_STOPFAIL: bool = True
    SB_STOPFQNT: int = 3

    SB_SENDER: str = "from@sender.com"
    SB_RECEIVERS: List[str] = field(default_factory=lambda: ["to@receiver.com"])
    SB_SERVER: str = "smtp.mail.com"
    SB_SUBJECT: str = "smtp-burst test"
    SB_BODY: str = "smtp-burst message body"
    SB_TEMPLATE: str = ""

    # Proxy and authentication defaults
    SB_PROXIES: List[str] = field(default_factory=list)
    SB_USERLIST: List[str] = field(default_factory=list)
    SB_PASSLIST: List[str] = field(default_factory=list)

    # Security options
    SB_SSL: bool = False
    SB_STARTTLS: bool = False

    # Delay options
    SB_GLOBAL_DELAY: float = 0.0
    SB_OPEN_SOCKETS_DELAY: float = 1.0
    SB_SMURF_DELAY: float = 0.01
    SB_TARPIT_THRESHOLD: float = 5.0

    # Data generation options
    SB_DATA_MODE: str = "ascii"
    SB_DICT_WORDS: List[str] = field(default_factory=list)
    SB_REPEAT_STRING: str = ""
    SB_PER_BURST_DATA: bool = False
    SB_SECURE_RANDOM: bool = False
    SB_RAND_STREAM: Optional[TextIO] = None
    SB_ENUM_LIST: List[str] = field(default_factory=list)

    SB_TEST_UNICODE: bool = False
    SB_TEST_UTF7: bool = False
    SB_TEST_TUNNEL: bool = False
    SB_TEST_CONTROL: bool = False

    @property
    def SB_TOTAL(self) -> int:
        """Total number of emails to send."""
        return self.SB_SGEMAILS * self.SB_BURSTS
