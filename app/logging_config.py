"""
Centralized logging configuration for the application.
"""

import logging
import sys

from app.config import get_settings


def configure_logging() -> None:
    """Configure root logging handlers/formatters once at startup."""
    settings = get_settings()

    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Already configured (e.g. reloaded module, tests) - avoid duplicates.
        root_logger.setLevel(settings.log_level)
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    root_logger.setLevel(settings.log_level)
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Convenience wrapper for module-level loggers."""
    return logging.getLogger(name)
