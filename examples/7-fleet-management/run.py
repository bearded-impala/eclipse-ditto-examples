#!/usr/bin/env python3
"""
Example 7: Fleet Management

## Goal

Manage a fleet of sensor devices.

## Flow

1. Create a policy for sensor devices
2. Bulk create multiple things from JSON files
3. Update sensor reported states
4. Search things with various filters
5. Combine search queries

This shows fleet management capabilities in Eclipse Ditto.
"""

import glob
import json
import os
import sys
from pathlib import Path

from utils.ditto_operations import (
    cleanup,
    create_policy,
    load_json_file,
    print_error,
    print_info,
    print_section,
    print_success,
    search_things,
    update_thing_property,
)


def bulk_create_things(current_dir: str = None) -> bool:
    """Bulk create things from JSON files in the fleet folder."""
    try:
        print_section("Bulk Creating Things")

        # Get the fleet folder path
        if current_dir:
            fleet_folder = Path(current_dir) / "fleet"
        else:
            # Fallback to current working directory
            fleet_folder = Path.cwd() / "fleet"

        # Get all JSON files in the fleet folder
        json_files = glob.glob(str(fleet_folder / "*.json"))

        if not json_files:
            print_error(f"No JSON files found in {fleet_folder}")
            return False

        print_info(f"Found {len(json_files)} sensor files to create")

        for json_file in sorted(json_files):
            try:
                # Load the JSON data
                thing_data = load_json_file(Path(json_file).name, str(fleet_folder))
                thing_id = thing_data.get("thingId")

                if not thing_id:
                    print_error(f"Skipping {json_file} - no 'thingId' found")
                    continue

                # Create the thing
                url = f"{os.getenv('DITTO_API_BASE', 'http://localhost:8080/api/2')}/things/{thing_id}"
                headers = {"Content-Type": "application/json"}
                auth = (
                    os.getenv("DITTO_USERNAME", "ditto"),
                    os.getenv("DITTO_PASSWORD", "ditto"),
                )

                import httpx

                session = httpx.Client(timeout=30.0)
                response = session.put(url, json=thing_data, auth=auth, headers=headers)

                if 200 <= response.status_code < 300:
                    print_success(f"Created {thing_id}")
                else:
                    print_error(
                        f"Failed to create {thing_id}. Status: {response.status_code}"
                    )
                    return False

                print_info("----------------------------")

            except Exception as e:
                print_error(f"Error processing {json_file}: {e}")
                return False

        return True

    except Exception as e:
        print_error(f"Error in bulk create: {e}")
        return False


def search_things_with_filter(
    filter_expr: str = None, description: str = "all things"
) -> bool:
    """
    Search things with optional filter.

    Args:
        filter_expr: Optional filter expression
        description: Description of the search for logging
    """
    try:
        print_section(f"Search: {description}")
        results = search_things(filter_expr)

        if results and results.get("items"):
            print_info(f"Found {len(results['items'])} things")
            print(json.dumps(results, indent=2))
            return True
        else:
            print_info("No results found")
            return True
    except Exception as e:
        print_error(f"Error searching things: {e}")
        return False


def main():
    """Main entry point for Fleet Management example."""
    try:
        # Get configuration from environment variables
        policy_id = os.getenv("SENSOR_POLICY_ID")
        sensor002_id = os.getenv("SENSOR_002_ID")

        if not policy_id or not sensor002_id:
            print_error(
                "Missing required environment variables: SENSOR_POLICY_ID or SENSOR_002_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 7: Fleet Management")
        print_info(
            "This example demonstrates fleet management capabilities in Eclipse Ditto"
        )
        print_info(f"Using policy ID: {policy_id}")
        print_info(f"Using sensor002 ID: {sensor002_id}")
        print_info(
            "This will create multiple sensors and demonstrate search capabilities"
        )

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 1: Create Policy
        if not create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 2: Bulk Create Things
        if not bulk_create_things(current_dir):
            print_error("Failed to bulk create things")
            sys.exit(1)

        # Step 3: Update sensor-002 reported state
        if not update_thing_property(
            sensor002_id, "features/humidity/properties/value", 70.1
        ):
            print_error("Failed to update sensor-002 humidity")
            sys.exit(1)

        # Step 4: Search Operations
        print_section("Search Operations")
        print_info("Demonstrating various search capabilities")

        # Search 1: Find all things
        if not search_things_with_filter(description="Find all things"):
            print_error("Failed to search all things")
            sys.exit(1)

        # Search 2: Find all things with manufacturer: 'ABC'
        if not search_things_with_filter(
            filter_expr="eq(attributes/manufacturer,'ABC')",
            description="Find all things with manufacturer: 'ABC'",
        ):
            print_error("Failed to search by manufacturer")
            sys.exit(1)

        # Search 3: Find all things where temperature > 20 Celsius
        if not search_things_with_filter(
            filter_expr="gt(features/temperature/properties/value,20)",
            description="Find all things where temperature > 20 Celsius",
        ):
            print_error("Failed to search by temperature")
            sys.exit(1)

        # Search 4: Find all things in the 'Living Room'
        if not search_things_with_filter(
            filter_expr="eq(attributes/location,'Living Room')",
            description="Find all things in the 'Living Room'",
        ):
            print_error("Failed to search by location")
            sys.exit(1)

        # Search 5: Combine queries (temperature > 20 AND location = 'Living Room')
        if not search_things_with_filter(
            filter_expr="and(gt(features/temperature/properties/value,20),eq(attributes/location,'Living Room'))",
            description="Combine queries (temperature > 20 AND location = 'Living Room')",
        ):
            print_error("Failed to search with combined filters")
            sys.exit(1)

        print_section("Example 7 completed successfully!")
        print_success("Fleet management example completed")
        print_info(
            "Multiple sensors were created and various search queries were demonstrated"
        )
        print_info("This shows how to manage large fleets of IoT devices")

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 7: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
