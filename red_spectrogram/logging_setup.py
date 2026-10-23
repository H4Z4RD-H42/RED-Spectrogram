"""File logging setup.

Windowed PyInstaller builds have no console, so anything printed is lost. A
rotating log file keeps the distributed build debuggable through
Help -> "Open Log File".
"""

from __future__ import annotations

import logging
import logging.handlers
import os

from .paths import get_data_dir

LOG_FILENAME = "red-spectrogram.log"


def get_log_path() -> str:
    return os.path.join(get_data_dir(), LOG_FILENAME)


def configure_logging(level: int = logging.INFO) -> str:
    """Attach a rotating file handler to the root logger. Returns the log file path."""
    log_path = get_log_path()

    try:
        handler: logging.Handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=2, encoding="utf-8"
        )
    except OSError:
        # Logging must never prevent the app from starting.
        handler = logging.NullHandler()

    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    return log_path
