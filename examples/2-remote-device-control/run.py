#!/usr/bin/env python3
"""
Example 2: Remote Device Control

## Goal

Send a command to a digital twin to change a desired state (e.g., turn a light on), and then verify the desired state is updated. For a real device, this would also involve the device receiving and acting on the command.

## Flow

1. Create a policy for a light device
2. Create a digital twin (thing) for the light
3. Update the desired state (onOff)
4. Retrieve the digital twin state

This shows the pattern of remote device control in Eclipse Ditto.
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
    """Main entry point for Remote Device Control example."""
    try:
        # Get configuration from environment variables
        light_id = os.getenv("LIGHT_001_ID")
        policy_id = os.getenv("LIGHT_001_POLICY_ID")

        if not light_id or not policy_id:
            print_error(
                "Missing required environment variables: LIGHT_001_ID or LIGHT_001_POLICY_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 2: Remote Device Control")
        print_info(
            "This example demonstrates remote device control using desired states"
        )
        print_info(f"Using light ID: {light_id}")
        print_info(f"Using policy ID: {policy_id}")

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 1: Create Policy
        if not create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 2: Create Thing
        if not create_thing(light_id, "thing.json", current_dir):
            print_error("Failed to create thing")
            sys.exit(1)

        # Step 3: Update Desired State (onOff)
        if not update_thing_property(
            light_id, "features/onOff/properties/status/desired", True
        ):
            print_error("Failed to update desired state")
            sys.exit(1)

        # Step 4: Retrieve Digital Twin State
        if not get_thing(light_id):
            print_error("Failed to retrieve thing")
            sys.exit(1)

        print_section("Example 2 completed successfully!")
        print_success("Remote device control example completed")
        print_info(
            "The light's desired state was updated and retrieved successfully"
        )
        print_info(
            "In a real scenario, the device would receive this command and turn on"
        )

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 2: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
