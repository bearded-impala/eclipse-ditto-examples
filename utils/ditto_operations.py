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
from typing import Any, Dict, Optional, Tuple

import httpx
import rich
from dotenv import load_dotenv
from kiota_abstractions.authentication import AuthenticationProvider
from kiota_abstractions.request_information import RequestInformation
from kiota_http.httpx_request_adapter import HttpxRequestAdapter

from ditto_client import BasicAuthProvider
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
DITTO_API_BASE = os.getenv("DITTO_API_BASE", "http://localhost:8080")
AUTH_TYPE = os.getenv("AUTH_TYPE", "BASIC").upper()  # "BASIC" or "BEARER"

AUTH_USER = os.getenv("DITTO_USERNAME", "ditto")
AUTH_PASS = os.getenv("DITTO_PASSWORD", "ditto")

JWT_ISSUER = os.getenv("JWT_ISSUER", "")
JWT_SUBJECT = os.getenv("JWT_SUBJECT", "ditto")


def _get_jwt_token(jwt_issuer: str, subject: str) -> Optional[str]:
    """Get a JWT token from the OAuth server (internal use only).

    Returns:
        JWT access token string, or None if retrieval fails
    """
    # Parse issuer - it might be "hostname:port/subject" or full URL
    if jwt_issuer.startswith("http://") or jwt_issuer.startswith("https://"):
        url = f"{jwt_issuer}/{subject}/token"
    else:
        # Assume format is "hostname:port/path"
        url = f"http://{jwt_issuer}/{subject}/token"
    
    data = {
        "grant_type": "client_credentials",
        "client_id": subject,
        "client_secret": "secret",
        "scope": "openid",
    }
    
    try:
        response = httpx.post(url, data=data, timeout=10.0)
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print_error(f"JWT token fetch failed: {e}")
        return None


def _determine_auth(token: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Resolve which auth method will be used based on AUTH_TYPE config and emit a log entry.

    Returns a tuple of (resolved_token, mode), where mode is one of
    "bearer-explicit", "bearer-env", or "basic".
    """
    # Explicit token always takes precedence
    if token:
        print_info("Auth mode: bearer (explicit token provided)")
        return token, "bearer-explicit"

    # Check AUTH_TYPE configuration
    if AUTH_TYPE == "BEARER":
        if not JWT_ISSUER:
            print_error("AUTH_TYPE=BEARER but JWT_ISSUER is not configured in .env")
            sys.exit(1)

        print_info(f"Auth mode: bearer (AUTH_TYPE=BEARER, issuer='{JWT_ISSUER}', subject='{JWT_SUBJECT}')")
        fetched_token = _get_jwt_token(JWT_ISSUER, JWT_SUBJECT)

        if fetched_token:
            return fetched_token, "bearer-env"
        print_error("Failed to fetch JWT token (AUTH_TYPE=BEARER does not fall back to basic auth)")
        sys.exit(1)
    
    # Default to basic auth
    print_info(f"Auth mode: basic (AUTH_TYPE={AUTH_TYPE})")
    return None, "basic"


class BearerTokenAuthProvider(AuthenticationProvider):
    """Authentication provider for Bearer token (JWT) authentication."""

    def __init__(self, token: str):
        self.token = token

    async def authenticate_request(
        self, request: RequestInformation, additional_authentication_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add Bearer token to request headers."""
        request.headers.try_add("Authorization", f"Bearer {self.token}")


async def _http_request(method: str, url: str, token: Optional[str] = None, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Make HTTP request with either JWT token or basic auth. Workaround for ditto-client serialization issues.
    
    Returns:
        Response JSON as dict
    """
    auth_type = "bearer token" if token else "basic auth"
    print_info(f"HTTP {method.upper()} {url} using {auth_type}")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if data:
        # Use merge-patch+json for PATCH operations, regular json for others
        if method.upper() == "PATCH":
            headers["Content-Type"] = "application/merge-patch+json"
        else:
            headers["Content-Type"] = "application/json"
    
    auth = None if token else (AUTH_USER, AUTH_PASS)

    async with httpx.AsyncClient(verify=False) as client:
        response = await client.request(method, url, headers=headers, json=data, auth=auth, timeout=30.0)
        response.raise_for_status()
        return response.json() if response.text else {}


def create_ditto_client(username: Optional[str] = None, password: Optional[str] = None, token: Optional[str] = None) -> DittoClient:
    """Create a new Ditto client instance.

    Returns:
        New DittoClient instance
    """
    resolved_token, mode = _determine_auth(token)

    if resolved_token:
        print_info(f"Creating Ditto client with bearer auth -> {DITTO_API_BASE}")
        auth_provider = BearerTokenAuthProvider(token=resolved_token)
    else:
        user = username or AUTH_USER
        pwd = password or AUTH_PASS
        print_info(f"Creating Ditto client with basic auth as '{user}' -> {DITTO_API_BASE}")
        auth_provider = BasicAuthProvider(user_name=user, password=pwd)

    request_adapter = HttpxRequestAdapter(auth_provider)
    request_adapter.base_url = DITTO_API_BASE
    return DittoClient(request_adapter)


def model_policy_from_json(policy_data: Dict[str, Any]) -> NewPolicy:
    """Create a NewPolicy object from JSON data."""
    # Create policy entries
    entries = PolicyEntries()
    
    if "policyId" in policy_data and "entries" in policy_data:
        entries.additional_data = policy_data["entries"]
    else:
        entries.additional_data = policy_data.get("entries", policy_data)

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

    Returns:
        Parsed JSON data
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


async def create_policy(policy_id: str, policy_file: str = "policy.json", example_dir: Optional[str] = None, token: Optional[str] = None) -> bool:
    """
    Create a policy from a JSON file.

    Returns:
        True if successful, False otherwise
    """
    try:
        policy_data = load_json_file(policy_file, example_dir)

        # Decide auth mode (env fetch allowed for convenience)
        resolved_token, mode = _determine_auth(token)

        # Use direct HTTP for both JWT and basic auth due to ditto-client serialization issues
        if "policyId" in policy_data:
            del policy_data["policyId"]
        await _http_request("PUT", f"{DITTO_API_BASE}/policies/{policy_id}", resolved_token, policy_data)

        print_success(f"Policy created: {policy_id}")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating policy {policy_id}: {e}")
        return False


async def create_thing(thing_id: str, thing_file: str = "thing.json", example_dir: Optional[str] = None, token: Optional[str] = None) -> bool:
    """
    Create a thing from a JSON file.

    Returns:
        True if successful, False otherwise
    """
    try:
        thing_data = load_json_file(thing_file, example_dir)

        resolved_token, mode = _determine_auth(token)

        # Use direct HTTP for both JWT and basic auth due to ditto-client serialization issues
        if "thingId" in thing_data:
            del thing_data["thingId"]
        await _http_request("PUT", f"{DITTO_API_BASE}/things/{thing_id}", resolved_token, thing_data)

        print_success(f"Thing created: {thing_id}")
        return True

    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False
    except Exception as e:
        print_error(f"Error creating thing {thing_id}: {e}")
        return False


async def update_thing_property(thing_id: str, path: str, value: Any, token: Optional[str] = None) -> bool:
    """
    Update a thing property using JSON merge patch.

    Returns:
        True if successful, False otherwise
    """
    try:
        resolved_token, mode = _determine_auth(token)
        
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

        # Use direct HTTP for both JWT and basic auth due to ditto-client serialization issues
        await _http_request("PATCH", f"{DITTO_API_BASE}/things/{thing_id}", resolved_token, current_dict)

        print_success(f"Updated {thing_id}/{path} = {value}")
        return True

    except Exception as e:
        print_error(f"Error updating {thing_id}/{path}: {e}")
        return False


async def get_thing(thing_id: str, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get a thing by ID.

    Returns:
        Thing data or None if not found
    """
    try:
        resolved_token, mode = _determine_auth(token)

        # Use direct HTTP for both JWT and basic auth due to ditto-client serialization issues
        thing_dict = await _http_request("GET", f"{DITTO_API_BASE}/things/{thing_id}", resolved_token)
        print_success(f"Retrieved thing: {thing_id}")
        rich.print(json.dumps(thing_dict, indent=2, default=str))
        return thing_dict

    except Exception as e:
        print_error(f"Error retrieving thing {thing_id}: {e}")
        return None


async def create_connection(connection_file: str = "connection.json", example_dir: Optional[str] = None) -> bool:
    """
    Create a connection from a JSON file using regular API.

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


async def search_things(filter_expr: Optional[str] = None, page_size: int = 200, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Search things with optional filter.

    Returns:
        Search results
    """
    try:
        resolved_token, mode = _determine_auth(token)

        # Build query parameters
        params = []
        if filter_expr:
            params.append(f"filter={filter_expr}")
        params.append(f"option=size({page_size})")
        query_string = "?" + "&".join(params) if params else ""
        
        url = f"{DITTO_API_BASE}/search/things{query_string}"
        response = await _http_request("GET", url, resolved_token)
        
        # Extract items from search response
        items = response.get("items", [])
        cursor = response.get("cursor")
        results = {"items": items, "cursor": cursor}
        print_success(f"Found {len(items)} things")
        return results

    except Exception as e:
        print_error(f"Error searching things: {e}")
        return {"items": [], "cursor": None}
