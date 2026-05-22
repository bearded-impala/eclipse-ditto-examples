#!/usr/bin/env python3
"""
Example: JWT authentication with the local mock OAuth server.

Fetches a bearer token from the mock OAuth service, creates a policy and thing,
then reads the thing back — all using the bearer token, not basic auth.

Run with: uv run poe e9-mock
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from utils.ditto_operations import create_policy, create_thing, get_thing

_NAMESPACE = os.getenv("DITTO_NAMESPACE", "org.eclipse.ditto")
_POLICY_ID = f"{_NAMESPACE}:sensor-policy-jwt"
_THING_ID = f"{_NAMESPACE}:sensor-jwt-001"


async def main() -> None:
    example_dir = Path(__file__).parent

    print("JWT Authentication Example with Ditto API\n")

    print("1. Creating policy...")
    if not await create_policy(_POLICY_ID, "policy.json", str(example_dir)):
        sys.exit(1)
    print(f"   Policy: {_POLICY_ID}\n")

    print("2. Creating thing...")
    thing_data = {
        "policyId": _POLICY_ID,
        "attributes": {
            "manufacturer": "JWT Demo",
            "model": "Test Thing",
            "created_with": "JWT authentication",
        },
        "features": {
            "temperature": {"properties": {"value": 23.5}},
        },
    }
    temp_file = example_dir / "temp_thing.json"
    temp_file.write_text(json.dumps(thing_data, indent=2))
    try:
        if not await create_thing(_THING_ID, temp_file.name, str(example_dir)):
            sys.exit(1)
        print(f"   Thing: {_THING_ID}\n")
    finally:
        temp_file.unlink(missing_ok=True)

    print("3. Retrieving thing...")
    if not await get_thing(_THING_ID):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
