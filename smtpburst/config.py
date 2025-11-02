from dataclasses import dataclass, field
from typing import Optional, TextIO

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
    SB_RETRY_COUNT: int = 0

    SB_SENDER: str = "from@sender.com"
    SB_RECEIVERS: list[str] = field(default_factory=lambda: ["to@receiver.com"])
    SB_SERVER: str = "smtp.mail.com"
    SB_HELO_HOST: str = ""
    SB_SUBJECT: str = "smtp-burst test"
    SB_BODY: str = "smtp-burst message body"
    SB_HTML_BODY: str = ""
    SB_TEMPLATE: str = ""

    # Proxy and authentication defaults
    SB_PROXIES: list[str] = field(default_factory=list)
    SB_PROXY_ORDER: str = "asc"
    SB_CHECK_PROXIES: bool = False
    SB_PROXY_TIMEOUT: float = 5.0
    SB_USERLIST: list[str] = field(default_factory=list)
    SB_PASSLIST: list[str] = field(default_factory=list)
    SB_USERNAME: str = ""
    SB_PASSWORD: str = ""

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
    SB_DICT_WORDS: list[str] = field(default_factory=list)
    SB_REPEAT_STRING: str = ""
    SB_PER_BURST_DATA: bool = False
    SB_SECURE_RANDOM: bool = False
    SB_RAND_STREAM: Optional[TextIO] = None
    SB_ENUM_LIST: list[str] = field(default_factory=list)

    # Connection timeout
    SB_TIMEOUT: float = 10.0

    SB_TEST_UNICODE: bool = False
    SB_TEST_UTF7: bool = False
    SB_TEST_TUNNEL: bool = False
    SB_TEST_CONTROL: bool = False
    SB_TEST_LONG_HEADERS: bool = False
    SB_TEST_NESTED_MULTIPART: bool = False
    SB_TEST_FILENAME_TRICK: bool = False
    SB_EICAR_TEST: bool = False
    SB_SMIME_SAMPLE: bool = False

    # Async sending options
    SB_ASYNC_NATIVE: bool = False
    SB_ASYNC_THREAD_OFFLOAD: bool = False
    SB_ASYNC_CONCURRENCY: int = 100
    SB_ASYNC_REUSE: bool = True
    SB_ASYNC_POOL_SIZE: int = 10
    SB_ASYNC_WARM_START: bool = False
    SB_ASYNC_COLD_START: bool = False

    # Trace header for deliverability workflows
    SB_TRACE_ID: str = ""
    SB_TRACE_HEADER: str = "X-Burst-ID"

    # Budget-based cancellation (seconds). 0 disables.
    SB_BUDGET_SECONDS: float = 0.0

    @property
    def SB_TOTAL(self) -> int:
        """Total number of emails to send."""
        return self.SB_SGEMAILS * self.SB_BURSTS
