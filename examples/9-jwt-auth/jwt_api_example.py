#!/usr/bin/env python3
"""
Example: Using JWT with Ditto API

This script demonstrates how to use a JWT token with the Ditto client library.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from utils.ditto_operations import create_policy, create_thing, get_thing


async def main():
    """Main function demonstrating JWT usage with Ditto client."""
    print("JWT Authentication Example with Ditto Client\n")
    
    # Configuration
    policy_id = os.getenv("SENSOR_POLICY_ID", "org.eclipse.ditto:sensor-policy")
    thing_id = f"{os.getenv('DITTO_NAMESPACE', 'org.eclipse.ditto')}:sensor-001"
    
    # Get current directory
    current_dir = str(Path(__file__).parent)
    
    # Example 1: Create policy (JWT auto-fetched internally)
    print("1. Creating policy...")
    if await create_policy(policy_id, "policy.json", current_dir):
        print(f"✓ Policy created: {policy_id}\n")
    else:
        print(f"✗ Policy creation failed\n")
        sys.exit(1)
    
    # Example 2: Create thing (JWT auto-fetched internally)
    print("2. Creating thing...")
    # Prepare thing data inline since we're not using a thing.json file
    thing_data = {
        "policyId": policy_id,
        "attributes": {
            "manufacturer": "JWT Demo",
            "model": "Test Thing",
            "created_with": "JWT authentication"
        },
        "features": {
            "temperature": {
                "properties": {"value": 23.5}
            }
        }
    }
    
    # Save thing data temporarily
    temp_thing_file = Path(current_dir) / "temp_thing.json"
    with open(temp_thing_file, "w") as f:
        json.dump(thing_data, f, indent=2)
    
    try:
        if await create_thing(thing_id, str(temp_thing_file.name), current_dir):
            print(f"✓ Thing created: {thing_id}\n")
        else:
            print(f"✗ Thing creation failed\n")
            sys.exit(1)
    finally:
        # Clean up temp file
        if temp_thing_file.exists():
            temp_thing_file.unlink()
    
    # Example 3: Retrieve thing
    print("3. Retrieving thing...")
    thing_result = await get_thing(thing_id)
    if thing_result:
        print(f"✓ Thing retrieved successfully\n")
    else:
        print(f"✗ Thing retrieval failed\n")
        sys.exit(1)
    
    print("✓ All examples completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
