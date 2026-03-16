import logging
import os
from datetime import datetime
from backend.utils.config import settings


def setup_logger(name: str = "ai_tutor") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    if logger.handlers:
        return logger

    os.makedirs(settings.log_dir, exist_ok=True)

    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_formatter = logging.Formatter(
        "%(levelname)s:     %(message)s"
    )

    file_handler = logging.FileHandler(
        os.path.join(settings.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log"),
        encoding="utf-8"
    )
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
