import logging
import os
import sys
from datetime import datetime, timedelta

LOG_DIR = "logs"
MAX_LINES = 300
os.makedirs(LOG_DIR, exist_ok=True)


def cleanup_old_logs(days=5):
    """
    Delete log files older than specified days from the logs directory.
    """
    cutoff = datetime.now() - timedelta(days=days)
    for filename in os.listdir(LOG_DIR):
        if not filename.endswith(".log"):
            continue
        filepath = os.path.join(LOG_DIR, filename)
        file_modified = datetime.fromtimestamp(os.path.getmtime(filepath))
        if file_modified < cutoff:
            os.remove(filepath)


def trim_log_file(filepath, max_lines=300):
    """
    Keep only the last max_lines lines in the log file.
    Runs on every startup to prevent log file growing too large.
    """
    if not os.path.exists(filepath):
        return
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) > max_lines:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(lines[-max_lines:])


# Clean old logs and trim current log on every startup
cleanup_old_logs(days=5)

log_filename = os.path.join(LOG_DIR, f"sync_{datetime.now().strftime('%Y-%m-%d')}.log")
trim_log_file(log_filename, max_lines=MAX_LINES)

# File handler — UTF-8
file_handler = logging.FileHandler(log_filename, encoding="utf-8")

# Console handler — force UTF-8 to avoid Windows charmap errors
console_handler = logging.StreamHandler(
    stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger = logging.getLogger("cosec_hrms_sync")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)