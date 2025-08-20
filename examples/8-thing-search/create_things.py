#!/usr/bin/env python3
"""
Simple thing creation script for Eclipse Ditto.
Creates a specified number of things by randomizing values from a schema.
"""

import argparse
import json
import random
import sys
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
    """Load schema from JSON file."""
    try:
        with open(schema_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        sys.exit(1)


def randomize_values(node: Any) -> Any:
    """Recursively randomize values in a schema node."""
    if isinstance(node, dict):
        return {k: randomize_values(v) for k, v in node.items()}
    elif isinstance(node, list):
        if not node:
            return []
        # If it's a list of lists, choose one of the inner lists
        if all(isinstance(i, list) for i in node):
            return random.choice(node)
        # Otherwise choose a random item from the list
        return random.choice(node)
    return node


def generate_thing_id(thing_type: str) -> str:
    """Generate a unique thing ID."""
    import uuid

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
        help="Path to schema file (default: schema/camera.json)",
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
            # Generate randomized thing data
            thing_data = randomize_values(schema.copy())

            # Generate unique thing ID
            thing_type = thing_data.get("attributes", {}).get("type", "thing")
            thing_id = generate_thing_id(thing_type)

            # Update thing ID and policy ID
            thing_data["thingId"] = thing_id
            thing_data["policyId"] = "org.eclipse.ditto:read-write-policy"

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
