#!/usr/bin/env python3
"""
Simplified Ditto utilities for educational examples.

This module provides simple functions for interacting with Eclipse Ditto
without the complexity of classes. Designed for educational purposes.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import httpx
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()

# Configuration
DITTO_URL = os.getenv("DITTO_API_BASE", "http://localhost:8080/api/2").rstrip("/")
AUTH_USER = os.getenv("DITTO_USERNAME", "ditto")
AUTH_PASS = os.getenv("DITTO_PASSWORD", "ditto")

# HTTP client session
_session = None


def get_session():
    """Get or create HTTP session."""
    global _session
    if _session is None:
        _session = httpx.Client(timeout=30.0)
    return _session


def close_session():
    """Close HTTP session."""
    global _session
    if _session:
        _session.close()
        _session = None


def print_section(title: str):
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(f"🔧 {title}")
    print("=" * 60)


def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"❌ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")


def load_json_file(filename: str, example_dir: str = None) -> Dict[str, Any]:
    """
    Load a JSON file from the current example directory.

    Args:
        filename: Name of the JSON file
        example_dir: Optional directory path (defaults to current script directory)

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        if example_dir:
            file_path = Path(example_dir) / filename
        else:
            # Get the directory of the calling script
            import inspect

            caller_frame = inspect.currentframe().f_back
            if caller_frame is None:
                # Fallback to current working directory
                file_path = Path.cwd() / filename
            else:
                caller_file = caller_frame.f_globals.get("__file__")
                if caller_file:
                    file_path = Path(caller_file).parent / filename
                else:
                    # Fallback to current working directory
                    file_path = Path.cwd() / filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r") as f:
            return json.load(f)

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {filename}: {e}")
        raise
    except Exception as e:
        print_error(f"Unexpected error loading {filename}: {e}")
        raise


def create_policy(
    policy_id: str, policy_file: str = "policy.json", example_dir: str = None
) -> bool:
    """
    Create a policy from a JSON file.

    Args:
        policy_id: The policy ID
        policy_file: Name of the policy JSON file
        example_dir: Optional directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        print_section(f"Creating Policy: {policy_id}")

        policy_data = load_json_file(policy_file, example_dir)
        url = f"{DITTO_URL}/policies/{policy_id}"
        headers = {"Content-Type": "application/json"}

        session = get_session()
        response = session.put(
            url, json=policy_data, auth=(AUTH_USER, AUTH_PASS), headers=headers
        )

        if 200 <= response.status_code < 300:
            print_success(f"Policy created: {policy_id}")
            return True
        else:
            print_error(
                f"Failed to create policy {policy_id}. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return False

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except httpx.RequestError as e:
        print_error(f"Network error creating policy {policy_id}: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error creating policy {policy_id}: {e}")
        return False


def create_thing(
    thing_id: str, thing_file: str = "thing.json", example_dir: str = None
) -> bool:
    """
    Create a thing from a JSON file.

    Args:
        thing_id: The thing ID
        thing_file: Name of the thing JSON file
        example_dir: Optional directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        print_section(f"Creating Thing: {thing_id}")

        thing_data = load_json_file(thing_file, example_dir)
        url = f"{DITTO_URL}/things/{thing_id}"
        headers = {"Content-Type": "application/json"}

        session = get_session()
        response = session.put(
            url, json=thing_data, auth=(AUTH_USER, AUTH_PASS), headers=headers
        )

        if 200 <= response.status_code < 300:
            print_success(f"Thing created: {thing_id}")
            return True
        else:
            print_error(
                f"Failed to create thing {thing_id}. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return False

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except httpx.RequestError as e:
        print_error(f"Network error creating thing {thing_id}: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error creating thing {thing_id}: {e}")
        return False


def update_thing_property(thing_id: str, path: str, value: Any) -> bool:
    """
    Update a thing property.

    Args:
        thing_id: The thing ID
        path: Property path (e.g., "features/temperature/properties/value")
        value: The value to set

    Returns:
        True if successful, False otherwise
    """
    try:
        print_section(f"Updating Property: {thing_id}/{path}")

        url = f"{DITTO_URL}/things/{thing_id}/{path}"
        headers = {"Content-Type": "application/json"}

        session = get_session()
        response = session.put(
            url, json=value, auth=(AUTH_USER, AUTH_PASS), headers=headers
        )

        if 200 <= response.status_code < 300:
            print_success(f"Updated {thing_id}/{path} = {value}")
            return True
        else:
            print_error(
                f"Failed to update {thing_id}/{path}. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return False

    except httpx.RequestError as e:
        print_error(f"Network error updating {thing_id}/{path}: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error updating {thing_id}/{path}: {e}")
        return False


def get_thing(thing_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a thing by ID.

    Args:
        thing_id: The thing ID

    Returns:
        Thing data or None if not found
    """
    try:
        print_section(f"Retrieving Thing: {thing_id}")

        url = f"{DITTO_URL}/things/{thing_id}"

        session = get_session()
        response = session.get(url, auth=(AUTH_USER, AUTH_PASS))

        if response.status_code == 200:
            thing_data = response.json()
            print_success(f"Retrieved thing: {thing_id}")
            print(json.dumps(thing_data, indent=2))
            return thing_data
        elif response.status_code == 404:
            print_error(f"Thing not found: {thing_id}")
            return None
        else:
            print_error(
                f"Failed to retrieve thing {thing_id}. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return None

    except httpx.RequestError as e:
        print_error(f"Network error retrieving thing {thing_id}: {e}")
        return None
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response for thing {thing_id}: {e}")
        return None
    except Exception as e:
        print_error(f"Unexpected error retrieving thing {thing_id}: {e}")
        return None


def create_connection(
    connection_file: str = "connection.json", example_dir: str = None
) -> bool:
    """
    Create a connection from a JSON file.

    Args:
        connection_file: Name of the connection JSON file
        example_dir: Optional directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        print_section("Creating Connection")

        connection_data = load_json_file(connection_file, example_dir)
        connection_timeout = os.getenv("CONNECTION_TIMEOUT", "60")

        # Use devops API for connections
        url = f"{os.getenv('DITTO_DEVOPS_API', 'http://localhost:8080/devops')}/piggyback/connectivity?timeout={connection_timeout}"
        headers = {"Content-Type": "application/json"}
        auth = (
            os.getenv("DITTO_DEVOPS_USERNAME", "devops"),
            os.getenv("DITTO_DEVOPS_PASSWORD", "foobar"),
        )

        session = get_session()
        response = session.post(url, json=connection_data, auth=auth, headers=headers)

        if 200 <= response.status_code < 300:
            print_success("Connection created successfully")
            return True
        else:
            print_error(f"Failed to create connection. Status: {response.status_code}")
            print_info(f"Response: {response.text}")
            return False

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except httpx.RequestError as e:
        print_error(f"Network error creating connection: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error creating connection: {e}")
        return False


def search_things(
    filter_expr: Optional[str] = None, page_size: int = 200
) -> Dict[str, Any]:
    """
    Search things with optional filter.

    Args:
        filter_expr: Optional filter expression
        page_size: Number of things per page

    Returns:
        Search results
    """
    try:
        search_url = f"{DITTO_URL}/search/things"
        params = {"option": f"size({page_size})"}

        if filter_expr:
            params["filter"] = filter_expr

        session = get_session()
        response = session.get(search_url, auth=(AUTH_USER, AUTH_PASS), params=params)

        if response.status_code == 200:
            results = response.json()
            print_success(f"Found {len(results.get('items', []))} things")
            return results
        else:
            print_error(f"Failed to search things. Status: {response.status_code}")
            print_info(f"Response: {response.text}")
            return {"items": [], "cursor": None}

    except httpx.RequestError as e:
        print_error(f"Network error searching things: {e}")
        return {"items": [], "cursor": None}
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON response from search: {e}")
        return {"items": [], "cursor": None}
    except Exception as e:
        print_error(f"Unexpected error searching things: {e}")
        return {"items": [], "cursor": None}


def cleanup():
    """Clean up resources."""
    close_session()
