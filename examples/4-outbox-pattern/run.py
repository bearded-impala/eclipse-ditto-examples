#!/usr/bin/env python3
"""
Example 4: Outbox Pattern

## Goal

Remotely lock/unlock a smart door. We want to ensure the command is eventually delivered and confirmed, even if the door lock is temporarily offline. We'll use the Outbox Pattern focusing on the desired vs. reported state synchronization.

## Flow

1. Create a policy for a doorlock device
2. Create a digital twin (thing) for the doorlock
3. Application issues command (sets desired state - Outbox)
4. Simulate device action and report (completing the outbox cycle)
5. Retrieve the digital twin state

This shows the outbox pattern for reliable command delivery.
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
    """Main entry point for Outbox Pattern example."""
    try:
        # Get configuration from environment variables
        doorlock_id = os.getenv("DOORLOCK_001_ID")
        policy_id = os.getenv("DOORLOCK_001_POLICY_ID")

        if not doorlock_id or not policy_id:
            print_error(
                "Missing required environment variables: DOORLOCK_001_ID or DOORLOCK_001_POLICY_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 4: Outbox Pattern")
        print_info(
            "This example demonstrates the outbox pattern for reliable command delivery"
        )
        print_info(f"Using doorlock ID: {doorlock_id}")
        print_info(f"Using policy ID: {policy_id}")
        print_info(
            "The outbox pattern ensures commands are delivered even when devices are offline"
        )

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 1: Create Policy
        if not create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 2: Create Thing
        if not create_thing(doorlock_id, "thing.json", current_dir):
            print_error("Failed to create thing")
            sys.exit(1)

        # Step 3: Application issues command (sets desired state - Outbox)
        if not update_thing_property(
            doorlock_id, "features/lockState/properties/status/desired", "LOCKED"
        ):
            print_error("Failed to set desired state")
            sys.exit(1)

        # Step 4: Simulate Device Action and Report (Completing the Outbox cycle)
        if not update_thing_property(
            doorlock_id, "features/lockState/properties/status/value", "LOCKED"
        ):
            print_error("Failed to update reported state")
            sys.exit(1)

        # Step 5: Retrieve Digital Twin State
        if not get_thing(doorlock_id):
            print_error("Failed to retrieve thing")
            sys.exit(1)

        print_section("Example 4 completed successfully!")
        print_success("Outbox pattern example completed")
        print_info("The doorlock command was issued and confirmed successfully")
        print_info(
            "This demonstrates reliable command delivery using desired vs reported states"
        )

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 4: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
