#!/usr/bin/env python3
"""
Simple thing creation script for Eclipse Ditto.
Creates a specified number of things by randomizing values from a schema.
"""

import argparse
import json
import random
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import httpx

# Determine important directories
THIS_FILE: Path = Path(__file__).resolve()
TEST_ROOT: Path = THIS_FILE.parent


def create_policy(
    client: httpx.Client, ditto_url: str, auth_user: str, auth_pass: str
) -> bool:
    """Create the required policy if it doesn't exist."""
    policy_id = "org.eclipse.ditto:read-write-policy"
    policy_data = {
        "entries": {
            "DEFAULT": {
                "subjects": {"{{ request:subjectId }}": {"type": "generated"}},
                "resources": {
                    "thing:/": {"grant": ["READ", "WRITE"], "revoke": []},
                    "policy:/": {"grant": ["READ", "WRITE"], "revoke": []},
                    "message:/": {"grant": ["READ", "WRITE"], "revoke": []},
                },
            }
        }
    }

    try:
        url = f"{ditto_url}/policies/{policy_id}"
        headers = {"Content-Type": "application/json"}

        response = client.put(
            url,
            json=policy_data,
            auth=(auth_user, auth_pass),
            headers=headers,
            timeout=30.0,
        )

        if 200 <= response.status_code < 300:
            print(f"✅ Policy created/updated: {policy_id}")
            return True
        else:
            print(
                f"❌ Failed to create policy {policy_id}. Status: {response.status_code}"
            )
            return False

    except Exception as e:
        print(f"❌ Error creating policy {policy_id}: {e}")
        return False


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load JSON schema from file."""
    try:
        with open(schema_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        sys.exit(1)


def generate_from_schema(schema: Dict[str, Any]) -> Any:
    """Generate data from a JSON schema with x-random-from extensions."""
    
    def generate_value(schema_node: Dict[str, Any]) -> Any:
        """Generate a value based on schema node."""
        # Check for custom randomization field
        if "x-random-from" in schema_node:
            return random.choice(schema_node["x-random-from"])
        
        # Handle const values
        if "const" in schema_node:
            return schema_node["const"]
        
        # Handle different types
        schema_type = schema_node.get("type", "string")
        
        if schema_type == "object":
            result = {}
            properties = schema_node.get("properties", {})
            required = schema_node.get("required", [])
            
            for prop_name, prop_schema in properties.items():
                if prop_name in required or random.random() > 0.3:  # Include most optional props
                    result[prop_name] = generate_value(prop_schema)
            return result
            
        elif schema_type == "array":
            items_schema = schema_node.get("items", {})
            # Generate 1-3 items for arrays unless x-random-from is specified
            if "x-random-from" in schema_node:
                return random.choice(schema_node["x-random-from"])
            else:
                array_length = random.randint(1, 3)
                return [generate_value(items_schema) for _ in range(array_length)]
                
        elif schema_type == "string":
            if schema_node.get("format") == "date-time":
                return datetime.now().isoformat() + "Z"
            elif schema_node.get("format") == "date":
                return datetime.now().strftime("%Y-%m-%d")
            elif "pattern" in schema_node:
                # For patterned strings like thingId, return a placeholder that will be overridden
                pattern = schema_node["pattern"]
                if "camera-" in pattern:
                    return "org.eclipse.ditto:camera-placeholder"
                else:
                    return f"generated_string_{random.randint(1000, 9999)}"
            else:
                return f"generated_string_{random.randint(1000, 9999)}"
                
        elif schema_type == "integer":
            return random.randint(1, 100)
            
        elif schema_type == "number":
            return round(random.uniform(0.1, 100.0), 2)
            
        elif schema_type == "boolean":
            return random.choice([True, False])
            
        else:
            return None
    
    return generate_value(schema)


def generate_thing_id(thing_type: str) -> str:
    """Generate a unique thing ID."""
    short_id = uuid.uuid4().hex[:6]
    return f"org.eclipse.ditto:{thing_type}-{short_id}"


def create_thing(
    client: httpx.Client,
    thing_id: str,
    thing_data: Dict[str, Any],
    ditto_url: str,
    auth_user: str,
    auth_pass: str,
) -> bool:
    """Create a single thing in Ditto."""
    try:
        url = f"{ditto_url}/things/{thing_id}"
        headers = {"Content-Type": "application/json"}

        response = client.put(
            url,
            json=thing_data,
            auth=(auth_user, auth_pass),
            headers=headers,
            timeout=30.0,
        )

        if 200 <= response.status_code < 300:
            print(f"✅ Created thing: {thing_id}")
            return True
        else:
            print(f"❌ Failed to create {thing_id}. Status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error creating {thing_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create things in Eclipse Ditto")
    parser.add_argument(
        "--count", type=int, required=True, help="Number of things to create"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="schema/camera.json",
        help="Path to JSON schema file (default: schema/camera.json)",
    )
    parser.add_argument(
        "--ditto-url",
        type=str,
        default="http://localhost:8080/api/2",
        help="Ditto API URL (default: http://localhost:8080/api/2)",
    )
    parser.add_argument(
        "--auth-user",
        type=str,
        default="ditto",
        help="Authentication username (default: ditto)",
    )
    parser.add_argument(
        "--auth-pass",
        type=str,
        default="ditto",
        help="Authentication password (default: ditto)",
    )

    args = parser.parse_args()

    # Load schema
    schema_path = TEST_ROOT / args.schema
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        sys.exit(1)

    schema = load_schema(schema_path)

    # Create HTTP client
    client = httpx.Client(timeout=30.0)

    print(f"🔧 Creating {args.count} things using schema: {schema_path}")
    print(f"🌐 Ditto URL: {args.ditto_url}")
    print("=" * 60)

    try:
        # Create policy first
        print("🔐 Creating policy...")
        if not create_policy(client, args.ditto_url, args.auth_user, args.auth_pass):
            print("❌ Failed to create policy. Exiting.")
            sys.exit(1)

        print()
        print("📦 Creating things...")
        success_count = 0

        for _i in range(args.count):
            # Generate data from JSON schema
            thing_data = generate_from_schema(schema)

            # Generate unique thing ID
            thing_type = thing_data.get("attributes", {}).get("type", "thing")
            thing_id = generate_thing_id(thing_type)

            # Update thing ID and policy ID (override schema values)
            thing_data["thingId"] = thing_id
            thing_data["policyId"] = "org.eclipse.ditto:read-write-policy"
            
            # Ensure timestamp is current
            if "attributes" in thing_data:
                thing_data["attributes"]["timestamp"] = datetime.now().isoformat() + "Z"

            # Create the thing
            if create_thing(
                client,
                thing_id,
                thing_data,
                args.ditto_url,
                args.auth_user,
                args.auth_pass,
            ):
                success_count += 1

    finally:
        client.close()

    print("=" * 60)
    print(f"✅ Successfully created {success_count}/{args.count} things")


if __name__ == "__main__":
    main()
