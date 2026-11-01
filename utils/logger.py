"""AutoLeadGen v2 - Robust Logging Module with File Rotation and Safe Tail Reading."""
import os
import logging
from logging.handlers import RotatingFileHandler
from config.settings import LOG_FILE

LOGGER_NAME = "AutoLeadGen"


def setup_logger(log_file=LOG_FILE, max_bytes=5 * 1024 * 1024, backup_count=5):
    """
    Configure and return logger with RotatingFileHandler and ConsoleHandler.
    Avoids unbounded log file growth.
    """
    log_dir = os.path.dirname(os.path.abspath(log_file))
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    app_logger = logging.getLogger(LOGGER_NAME)
    app_logger.setLevel(logging.INFO)

    if not app_logger.handlers:
        # Rotating File Handler (Max 5MB per file, keep 5 backups, UTF-8)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        app_logger.addHandler(file_handler)
        app_logger.addHandler(console_handler)

    return app_logger


logger = setup_logger()


def info(message: str):
    logger.info(message)


def warning(message: str):
    logger.warning(message)


def error(message: str):
    logger.error(message)


def critical(message: str):
    logger.critical(message)


def audit(action: str, details: str = ""):
    logger.info(f"AUDIT | {action} | {details}")


def read_recent_logs(log_file=LOG_FILE, max_bytes=25000) -> str:
    """
    Safely read only the last `max_bytes` of the log file without loading
    the entire file into memory.
    """
    if not os.path.exists(log_file):
        return "No logs recorded yet."

    try:
        size = os.path.getsize(log_file)
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                # Discard partial line
                f.readline()
            return f.read()
    except Exception as ex:
        return f"Error reading log file: {ex}"
