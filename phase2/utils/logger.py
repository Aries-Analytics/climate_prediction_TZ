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
    Configure project-wide logging (console + rotating timestamped file).

    Args:
        level: logging level (e.g., logging.INFO or logging.DEBUG)
        retention_days: delete log files older than this many days
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


def log_error(msg: str):
    logging.getLogger().error(msg)
