"""
Shared utilities for Eclipse Ditto examples.

This package contains common utilities used across multiple Ditto example projects:
- Configuration and environment setup
- HTTP client for Ditto API
- Data generation utilities
- Bulk operations
- Logging utilities
- Performance benchmarking utilities
"""

from .config import Config, load_config
from .http_client import DittoClient, create_ditto_client
from .logging_utils import ColorFormatter, color_result_line, setup_logging

__version__ = "0.1.0"
__all__ = [
    # Config
    "load_config",
    "Config",
    # HTTP Client
    "DittoClient",
    "create_ditto_client",
    # Logging
    "setup_logging",
    "ColorFormatter",
    "color_result_line",
]
