# Ditto Utils

This package contains shared utilities for Eclipse Ditto examples, providing common functionality used across multiple example projects.

## Overview

The utils package consolidates common functionality used across Ditto examples:

- **Configuration management**: Environment variables and file paths
- **HTTP client**: Ditto API interactions
- **Data generation**: Thing descriptor generation and random data
- **Bulk operations**: Fleet creation and cleanup
- **Validation utilities**: Configuration and data validation
- **Logging utilities**: Colored output and formatting
- **Performance utilities**: Benchmarking decorators and tools

## Structure

```
utils/
├── __init__.py         # Package initialization and exports
├── config.py           # Configuration management
├── http_client.py      # HTTP client for Ditto API
├── data_generation.py  # Data generation utilities
├── bulk_operations.py  # Bulk operations (create/delete)
├── validation.py       # Configuration and data validation
├── logging_utils.py    # Logging setup and formatting
├── perf.py            # Performance benchmarking utilities
└── README.md          # This file
```

## Usage

### As a Local Package

This package can be installed as a local dependency in other examples:

```bash
# From the examples directory
uv add --editable ./utils
```

### Basic Setup

```python
from utils import load_config, create_ditto_client, setup_logging

# Load configuration
config = load_config()

# Setup logging
logger = setup_logging()

# Create client
client = create_ditto_client(config)
```

### Performance Testing

```python
from utils import benchmark_to_csv

@benchmark_to_csv("my_test", out_dir="results")
def my_function():
    # Your code here
    return {"status": "success"}
```