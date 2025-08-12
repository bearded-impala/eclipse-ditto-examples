"""
Configuration utilities for Eclipse Ditto examples.

This module provides configuration management for connecting to Eclipse Ditto APIs
and is used across multiple example projects in this repository.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration for Ditto API connection and common settings."""

    ditto_url: str
    auth_user: str
    auth_pass: str
    count: int

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from environment variables."""
        # Load environment variables
        load_dotenv()

        return cls(
            ditto_url=os.getenv("DITTO_API_BASE", "http://localhost:8080/api/2"),
            auth_user=os.getenv("DITTO_USERNAME", "ditto"),
            auth_pass=os.getenv("DITTO_PASSWORD", "ditto"),
            count=int(os.getenv("BENCHMARK_COUNT", "5")),
        )


def load_config() -> Config:
    """
    Load configuration for Eclipse Ditto examples.

    Returns:
        Config instance with loaded values
    """
    return Config.load()
