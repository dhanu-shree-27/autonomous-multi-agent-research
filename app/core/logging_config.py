"""
Centralized logging setup.

Why this matters for this project specifically: from Phase 2 onward, every
agent call (Planner, Researcher, Fact Checker, Synthesizer, Report
Generator) needs to be logged so the workflow is traceable — this is the
"Agent Tracing" requirement from the architecture doc. Setting up logging
properly now in Phase 1 means every future phase just calls
`logging.getLogger(__name__)` and gets consistent, readable output for
free — both in the console and in a log file you can show during your
viva.
"""

import logging
import sys
from pathlib import Path

from app.core.config import settings

LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"


def setup_logging() -> None:
    """Configures root logging once, at application startup."""
    LOG_DIR.mkdir(exist_ok=True)

    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Avoid adding duplicate handlers if setup_logging() is called more than once
    # (e.g. during tests, or with an auto-reloading dev server).
    if root_logger.handlers:
        return

    formatter = logging.Formatter(log_format, datefmt=date_format)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
