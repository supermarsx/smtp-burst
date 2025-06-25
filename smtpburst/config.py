"""Configuration utilities for smtp-burst."""

from __future__ import annotations

from dataclasses import dataclass, field

# Size constants
SZ_KILOBYTE = 1024
SZ_MEGABYTE = 1024 * SZ_KILOBYTE
SZ_GIGABYTE = 1024 * SZ_MEGABYTE
SZ_TERABYTE = 1024 * SZ_GIGABYTE


@dataclass
class Config:
    """Runtime configuration values."""

    # Message options
    server: str = "smtp.mail.com"
    sender: str = "from@sender.com"
    receivers: list[str] = field(default_factory=lambda: ["to@receiver.com"])
    subject: str = "smtp-burst test"
    body: str = "smtp-burst message body"

    # Burst behaviour
    emails_per_burst: int = 5
    email_delay: float = 1.0
    bursts: int = 3
    burst_delay: float = 3.0

    # Message size and failure handling
    size: int = 5 * SZ_MEGABYTE * 2
    stop_on_fail: bool = True
    stop_fail_count: int = 3

    # Proxy and authentication settings
    proxies: list[str] = field(default_factory=list)
    userlist: list[str] = field(default_factory=list)
    passlist: list[str] = field(default_factory=list)

    # Security options
    ssl: bool = False
    starttls: bool = False

    @property
    def total(self) -> int:
        """Total number of emails that will be sent."""
        return self.emails_per_burst * self.bursts
