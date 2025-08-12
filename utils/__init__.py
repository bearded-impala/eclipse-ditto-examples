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
from .data_generation import *
from .bulk_operations import *
from .logging_utils import *
from .validation import *
from .perf import *
from .paths import *

__version__ = "0.1.0"
__all__ = [
    # Config
    "load_config",
    "Config",
    
    # HTTP Client
    "DittoClient",
    "create_ditto_client",
    
    # Data Generation
    "generate_short_uuid",
    "generate_sample_from_schema",
    "generate_thing_descriptor",
    "generate_thing_descriptor_from_json_schema",
    "load_policy",
    
    # Bulk Operations
    "collect_thing_ids_with_progress",
    "delete_all_things_parallel",
    "spawn_fleet",
    
    # Logging
    "setup_logging",
    "ColorFormatter",
    "color_result_line",

    # Validation
    "validate_config",
    "validate_schema_file",
    "validate_policy_file",
    "validate_thing_data",
    "validate_query_expression",
    "print_validation_errors",
    "detect_schema_type",
    "ensure_feature_properties",
    
    # Performance
    "benchmark_to_csv",
    "benchmark_concurrent_requests",
    "benchmark_parallel_requests", 
    "save_benchmark_results",
    "print_benchmark_summary",
    
    # Path utilities
    "get_project_root",
    "get_script_dir",
    "find_file_in_paths",
    "find_schema_file",
    "find_policy_file",
    "ensure_directory",
    "get_safe_filename",
    "resolve_relative_path",
] 