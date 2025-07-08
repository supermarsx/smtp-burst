"""smtp-burst library package."""

# Package version
__version__ = "0.1.0"

from . import (
    send,
    config,
    cli,
    datagen,
    attacks,
    discovery,
    reporting,
    inbox,
    pipeline,
    proxy,
)

__all__ = [
    "send",
    "config",
    "cli",
    "datagen",
    "attacks",
    "discovery",
    "reporting",
    "inbox",
    "pipeline",
    "proxy",
]
