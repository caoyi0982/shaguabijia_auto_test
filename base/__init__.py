import logging
import os
from logging.handlers import TimedRotatingFileHandler

from config import BASE_DIR

_logger = logging.getLogger("shaguabijia")
if not _logger.handlers:
    _logger.setLevel(logging.INFO)
    log_dir = os.path.join(BASE_DIR, "log")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, "web.log"),
        when="midnight",
        interval=1,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(filename)s(%(funcName)s:%(lineno)d)] - %(message)s"
    )
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

log = _logger
