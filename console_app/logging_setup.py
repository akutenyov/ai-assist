"""Private diagnostic logging configuration."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


PROJECT_DIRECTORY = Path(__file__).resolve().parent.parent


def configure_logging() -> logging.Logger:
    """Create a rotating log without recording prompts, replies, or secrets."""
    logger = logging.getLogger("ai_assist")

    if logger.handlers:
        return logger

    log_directory = PROJECT_DIRECTORY / "logs"
    log_directory.mkdir(exist_ok=True)
    handler = RotatingFileHandler(
        log_directory / "ai_assist.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False

    return logger


LOGGER = configure_logging()
