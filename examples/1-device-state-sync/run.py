#!/usr/bin/env python3
"""
Example 1: Device State Sync

## Goal

- Send a command to a digital twin to change a desired state (e.g., turn a light on), and then verify the desired state is updated.
- For a real device, this would also involve the device receiving and acting on the command.

## Flow

1. Create a policy for a sensor device
2. Create a digital twin (thing) for the sensor
3. Update the reported state (temperature)
4. Retrieve the digital twin state

This shows the basic pattern of device state synchronization in Eclipse Ditto.
"""

import os
import sys

from utils.ditto_operations import (
    cleanup,
    create_policy,
    create_thing,
    get_thing,
    print_error,
    print_info,
    print_section,
    print_success,
    update_thing_property,
)


def main():
    """Main entry point for Device State Sync example."""
    try:
        # Get configuration from environment variables
        sensor_id = os.getenv("SENSOR_001_ID")
        policy_id = os.getenv("SENSOR_001_POLICY_ID")

        if not sensor_id or not policy_id:
            print_error(
                "Missing required environment variables: SENSOR_001_ID or SENSOR_001_POLICY_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 1: Device State Sync")
        print_info("This example demonstrates basic device state synchronization")
        print_info(f"Using sensor ID: {sensor_id}")
        print_info(f"Using policy ID: {policy_id}")

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 1: Create Policy
        if not create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 2: Create Thing
        if not create_thing(sensor_id, "thing.json", current_dir):
            print_error("Failed to create thing")
            sys.exit(1)

        # Step 3: Update Reported State (temperature)
        if not update_thing_property(
            sensor_id, "features/temperature/properties/value", 22.8
        ):
            print_error("Failed to update temperature")
            sys.exit(1)

        # Step 4: Retrieve Digital Twin State
        if not get_thing(sensor_id):
            print_error("Failed to retrieve thing")
            sys.exit(1)

        print_section("Example 1 completed successfully!")
        print_success("Device state synchronization example completed")
        print_info("The sensor's temperature was updated and retrieved successfully")

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 1: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
