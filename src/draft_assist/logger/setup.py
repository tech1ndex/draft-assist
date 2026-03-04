import sys

from loguru import logger


def setup_logger() -> "logger":
    logger.remove()
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss} - {level} - {message}",
        level="INFO",
    )
    return logger
