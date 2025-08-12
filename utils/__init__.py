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

from .config import *
from .http_client import *
from .logging_utils import *

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