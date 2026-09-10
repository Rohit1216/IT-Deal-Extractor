"""
Logging setup for the Deal Research Engine.

Rule: never log API keys or full .env contents. Callers should log
"API key configured" (boolean) rather than the key value itself.
"""

from __future__ import annotations

import logging
import sys

_CONFIGURED = False


def get_logger(name: str = "deal_research_engine") -> logging.Logger:
    global _CONFIGURED
    logger = logging.getLogger(name)

    if not _CONFIGURED:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)

        root = logging.getLogger("deal_research_engine")
        root.setLevel(logging.INFO)
        root.addHandler(handler)
        root.propagate = False
        _CONFIGURED = True

    return logger
