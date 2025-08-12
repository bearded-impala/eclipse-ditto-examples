"""
Logging utilities for Eclipse Ditto examples.

This module provides logging utilities with colored output support for
Eclipse Ditto examples and is used across multiple example projects
in this repository.
"""

import logging

from colorama import Fore, Style
from colorama import init as colorama_init

# Initialize colorama for cross-platform colored output
colorama_init(autoreset=True)


class ColorFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""

    def format(self, record):
        msg = super().format(record)
        if record.levelno == logging.ERROR:
            return f"{Fore.RED}{msg}{Style.RESET_ALL}"
        elif record.levelno == logging.WARNING:
            return f"{Fore.YELLOW}{msg}{Style.RESET_ALL}"
        elif record.levelno == logging.INFO:
            return f"{Fore.CYAN}{msg}{Style.RESET_ALL}"
        return msg


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Setup colored logging for the application.

    Args:
        level: Logging level

    Returns:
        Configured logger instance
    """
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))

    logger = logging.getLogger(__name__)
    logger.handlers = []
    logger.addHandler(handler)
    logger.setLevel(level)

    # Suppress httpx logging
    logging.getLogger("httpx").setLevel(logging.WARNING)

    return logger


def color_result_line(line: str, status_code: int) -> str:
    """
    Color a result line based on HTTP status code.

    Args:
        line: Line to color
        status_code: HTTP status code

    Returns:
        Colored line
    """
    if 200 <= status_code < 300:
        return f"{Fore.GREEN}{line}{Style.RESET_ALL}"
    elif 400 <= status_code < 500:
        return f"{Fore.YELLOW}{line}{Style.RESET_ALL}"
    elif 500 <= status_code < 600:
        return f"{Fore.RED}{line}{Style.RESET_ALL}"
    return line


def setup_basic_logging() -> logging.Logger:
    """
    Setup basic logging without colors (for scripts that don't need colors).

    Returns:
        Configured logger instance
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger(__name__)
