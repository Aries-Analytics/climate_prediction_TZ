"""
utils/logger.py

Centralized logging utility for the Tanzania Climate Prediction pipeline.
Provides:
 - setup_logging(level=logging.INFO, retention_days=7)
 - get_logger(name)
 - log_info / log_error wrappers

This implementation creates a timestamped daily log file in ./logs/,
uses a RotatingFileHandler, and cleans up old logs older than retention_days.
"""

import logging
import os
import sys
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"


def setup_logging(level=logging.INFO, retention_days: int = 7):
    """
    Configure project-wide logging with console and file output.

    Sets up centralized logging for the entire pipeline with timestamped daily log files,
    automatic rotation, and cleanup of old logs.

    Parameters
    ----------
    level : int, optional
        Logging level (e.g., logging.INFO, logging.DEBUG, logging.WARNING).
        Default is logging.INFO.
    retention_days : int, optional
        Number of days to retain log files. Files older than this are automatically deleted.
        Default is 7 days.

    Returns
    -------
    logging.Logger
        Configured root logger instance.

    Notes
    -----
    **Log File Management:**

    - Creates timestamped log files: logs/pipeline_YYYY-MM-DD.log
    - Rotating file handler with 5MB max size and 3 backups
    - Automatic cleanup of logs older than retention_days
    - Console output to stdout

    **Log Format:**

    .. code-block:: text

        YYYY-MM-DD HH:MM:SS | LEVEL | module_name | Message

    **Directory Structure:**

    - Log directory: logs/
    - Log files: pipeline_YYYY-MM-DD.log
    - Backup files: pipeline_YYYY-MM-DD.log.1, .2, .3

    Examples
    --------
    >>> import logging
    >>> from utils.logger import setup_logging
    >>>
    >>> # Setup with INFO level (default)
    >>> logger = setup_logging()
    >>>
    >>> # Setup with DEBUG level for verbose output
    >>> logger = setup_logging(level=logging.DEBUG)
    >>>
    >>> # Setup with custom retention period
    >>> logger = setup_logging(level=logging.INFO, retention_days=30)
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    # --- cleanup old logs ---
    cutoff = datetime.now() - timedelta(days=retention_days)
    for fname in os.listdir(LOG_DIR):
        if fname.startswith("pipeline_") and fname.endswith(".log"):
            try:
                date_part = fname.split("_", 1)[1].split(".")[0]
                file_date = datetime.strptime(date_part, "%Y-%m-%d")
                if file_date < cutoff:
                    try:
                        os.remove(os.path.join(LOG_DIR, fname))
                    except Exception:
                        pass
            except Exception:
                # ignore files with unexpected names
                continue

    # --- timestamped log filename for today ---
    timestamp = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(LOG_DIR, f"pipeline_{timestamp}.log")

    # Create handlers
    rotating_handler = RotatingFileHandler(log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    console_handler = logging.StreamHandler(sys.stdout)

    # Formatter
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    rotating_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root = logging.getLogger()
    # Remove all existing handlers to avoid duplicate logs
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(level)
    root.addHandler(rotating_handler)
    root.addHandler(console_handler)

    root.info(f"Logging initialized: {os.path.basename(log_file)} (level={logging.getLevelName(level)})")
    return root


def get_logger(name=__name__):
    """Return a logger for the given name. Call setup_logging(...) first to configure handlers."""
    return logging.getLogger(name)


# convenience wrappers used across the codebase
def log_info(msg: str):
    logging.getLogger().info(msg)


def log_warning(msg: str):
    logging.getLogger().warning(msg)


def log_error(msg: str):
    logging.getLogger().error(msg)
