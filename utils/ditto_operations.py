#!/usr/bin/env python3
"""
Simplified Ditto utilities for educational examples.

This module provides simple functions for interacting with Eclipse Ditto
without the complexity of classes. Designed for educational purposes.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import rich
from dotenv import load_dotenv
from kiota_http.httpx_request_adapter import HttpxRequestAdapter

from ditto_client.basic_auth import BasicAuthProvider
from ditto_client.generated.ditto_client import DittoClient
from ditto_client.generated.models.new_policy import NewPolicy
from ditto_client.generated.models.new_thing import NewThing
from ditto_client.generated.models.policy_entries import PolicyEntries
from ditto_client.generated.models.attributes import Attributes
from ditto_client.generated.models.features import Features
from ditto_client.generated.models.patch_thing import PatchThing
from ditto_client.generated.models.new_connection import NewConnection
from ditto_client.generated.models.base_piggyback_command_request_schema import BasePiggybackCommandRequestSchema

load_dotenv()

# Configuration
DITTO_BASE_URL = os.getenv("DITTO_BASE_URL", "http://localhost:8080")

AUTH_USER = os.getenv("DITTO_USERNAME", "ditto")
AUTH_PASS = os.getenv("DITTO_PASSWORD", "ditto")


def create_ditto_client(username: Optional[str] = None, password: Optional[str] = None) -> DittoClient:
    """Create a new Ditto client instance.

    Args:
        username: Optional username (defaults to AUTH_USER)
        password: Optional password (defaults to AUTH_PASS)

    Returns:
        New DittoClient instance
    """
    user = username or AUTH_USER
    pwd = password or AUTH_PASS

    auth_provider = BasicAuthProvider(user_name=user, password=pwd)
    request_adapter = HttpxRequestAdapter(auth_provider)
    request_adapter.base_url = DITTO_BASE_URL
    return DittoClient(request_adapter)


def model_policy_from_json(policy_data: Dict[str, Any]) -> NewPolicy:
    """Create a NewPolicy object from JSON data."""
    # Create policy entries
    entries = PolicyEntries()
    entries.additional_data = policy_data.get("entries", {})

    # Create the policy
    policy = NewPolicy()
    policy.entries = entries

    return policy


def model_thing_from_json(thing_data: Dict[str, Any]) -> NewThing:
    """Create a NewThing object from JSON data."""
    thing = NewThing()
    thing.policy_id = thing_data.get("policyId")

    # Handle attributes
    if "attributes" in thing_data:
        attributes = Attributes()
        attributes.additional_data = thing_data["attributes"]
        thing.attributes = attributes

    # Handle features
    if "features" in thing_data:
        features = Features()
        features.additional_data = thing_data["features"]
        thing.features = features

    return thing

def print_section(title: str) -> None:
    """Print a formatted section header."""
    rich.print("=" * 60)
    rich.print(f"-- {title} --")
    rich.print("=" * 60)

def print_success(message: str) -> None:
    """Print a success message."""
    rich.print(f"[SUCCESS] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    rich.print(f"[ERROR] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    rich.print(f"[INFO] {message}")


def load_json_file(filename: str, directory: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a JSON file from the specified directory.

    Args:
        filename: Name of the JSON file
        directory: Directory path (defaults to current working directory)

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    try:
        if directory:
            file_path = Path(directory) / filename
        else:
            file_path = Path(filename)  # Assume filename includes path or is in cwd

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r") as f:
            data: Dict[str, Any] = json.load(f)
            return data

    except FileNotFoundError as e:
        print_error(f"File not found: {e}")
        raise
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in {filename}: {e}")
        raise
    except Exception as e:
        print_error(f"Unexpected error loading {filename}: {e}")
        raise


async def create_policy(policy_id: str, policy_file: str = "policy.json", example_dir: Optional[str] = None) -> bool:
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
        policy_data = load_json_file(policy_file, example_dir)
        policy_obj = model_policy_from_json(policy_data)

        ditto_client = create_ditto_client()

        # Use the Ditto client to create policy
        await ditto_client.api.two.policies.by_policy_id(policy_id).put(policy_obj)

        print_success(f"Policy created: {policy_id}")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating policy {policy_id}: {e}")
        return False


async def create_thing(thing_id: str, thing_file: str = "thing.json", example_dir: Optional[str] = None) -> bool:
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
        thing_data = load_json_file(thing_file, example_dir)
        thing_obj = model_thing_from_json(thing_data)

        ditto_client = create_ditto_client()

        # Use the Ditto client to create thing
        await ditto_client.api.two.things.by_thing_id(thing_id).put(thing_obj)

        print_success(f"Thing created: {thing_id}")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating thing {thing_id}: {e}")
        return False


async def update_thing_property(thing_id: str, path: str, value: Any) -> bool:
    """
    Update a thing property using JSON merge patch.

    Args:
        thing_id: The thing ID
        path: Property path (e.g., "attributes/manufacturer" or "features/temperature/properties/value")
        value: The value to set

    Returns:
        True if successful, False otherwise
    """
    try:
        ditto_client = create_ditto_client()

        patch_data = PatchThing()

        # Build the nested structure based on the path
        path_parts = path.split("/")
        current_dict: Dict[str, Any] = {}
        target_dict = current_dict

        # Navigate to the target location
        for part in path_parts[:-1]:
            target_dict[part] = {}
            target_dict = target_dict[part]

        # Set the final value
        target_dict[path_parts[-1]] = value

        # Set the patch data
        patch_data.additional_data = current_dict

        # Use the Ditto client to update property
        await ditto_client.api.two.things.by_thing_id(thing_id).patch(patch_data)

        print_success(f"Updated {thing_id}/{path} = {value}")
        return True

    except Exception as e:
        print_error(f"Error updating {thing_id}/{path}: {e}")
        return False


async def get_thing(thing_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a thing by ID.

    Args:
        thing_id: The thing ID

    Returns:
        Thing data or None if not found
    """
    try:
        ditto_client = create_ditto_client()

        # Use the Ditto client to get thing
        thing_data = await ditto_client.api.two.things.by_thing_id(thing_id).get()

        print_success(f"Retrieved thing: {thing_id}")

        # Convert Thing object to dict for display
        try:
            if hasattr(thing_data, "__dict__"):
                thing_dict: Dict[str, Any] = thing_data.__dict__
            else:
                thing_dict = {"thing_id": thing_id, "data": str(thing_data)}

            rich.print(json.dumps(thing_dict, indent=2, default=str))
            return thing_dict
        except Exception as json_error:
            print_info(f"Could not serialize thing data: {json_error}")
            rich.print(f"Thing data: {thing_data}")
            return {"thing_id": thing_id, "data": str(thing_data)}

    except Exception as e:
        print_error(f"Error retrieving thing {thing_id}: {e}")
        return None


async def create_connection(connection_file: str = "connection.json", example_dir: Optional[str] = None) -> bool:
    """
    Create a connection from a JSON file using regular API.

    Args:
        connection_file: Name of the connection JSON file
        example_dir: Optional directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        devops_ditto_client = create_ditto_client(username="devops", password="foobar")
        connection_data = load_json_file(connection_file, example_dir)

        # Extract the actual connection data from the piggyback format
        if "piggybackCommand" in connection_data and "connection" in connection_data["piggybackCommand"]:
            connection_config = connection_data["piggybackCommand"]["connection"]
        else:
            # If it's already in the right format, use it directly
            connection_config = connection_data.copy()

        # Remove the ID since the regular API generates it automatically
        if "id" in connection_config:
            del connection_config["id"]

        connection_obj = NewConnection()

        # For now, put everything in additional_data to avoid serialization issues
        connection_obj.additional_data = connection_config

        # Use the regular API to create connection (POST generates ID automatically)
        await devops_ditto_client.api.two.connections.post(connection_obj)

        print_success("Connection created successfully via regular API")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating connection: {e}")
        return False


async def create_connection_piggyback(
    connection_file: str = "connection.json", example_dir: Optional[str] = None
) -> bool:
    """
    Create a connection from a JSON file using DevOps API piggyback.

    Args:
        connection_file: Name of the connection JSON file
        example_dir: Optional directory path

    Returns:
        True if successful, False otherwise
    """
    try:
        devops_ditto_client = create_ditto_client(username="devops", password="foobar")
        connection_data = load_json_file(connection_file, example_dir)

        piggyback_command = BasePiggybackCommandRequestSchema()
        piggyback_command.additional_data = connection_data

        # Use the DevOps API to create connection
        # We need to send it to the connectivity service via piggyback
        await devops_ditto_client.devops.piggyback.by_service_name("connectivity").post(piggyback_command)

        print_success("Connection created successfully via piggyback")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating connection via piggyback: {e}")
        return False


async def search_things(filter_expr: Optional[str] = None, page_size: int = 200) -> Dict[str, Any]:
    """
    Search things with optional filter.

    Args:
        filter_expr: Optional filter expression
        page_size: Number of things per page

    Returns:
        Search results
    """
    try:
        ditto_client = create_ditto_client()

        # Use the Ditto client to search things
        response = await ditto_client.api.two.things.get()

        # Handle PyPI client response format - returns simple list
        items: list[Any] = []
        if response is not None:
            if isinstance(response, list):
                # PyPI version returns a simple list
                items = response
            elif hasattr(response, "items") and response.items is not None:
                # Fallback for other response formats
                items = list(response.items)
            else:
                # If no items attribute, treat the response as a single item
                items = [response]

        results = {"items": items, "cursor": None}
        print_success(f"Found {len(items)} things")
        return results

    except Exception as e:
        print_error(f"Error searching things: {e}")
        return {"items": [], "cursor": None}

