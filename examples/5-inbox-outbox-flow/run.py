#!/usr/bin/env python3
"""
Example 5: Inbox Outbox Flow

## Goal

Simulate an application polling a Smart Kettle's digital twin to:
1. Check if a desired temperature command is pending (outbox concept).
2. Read the latest reported temperature and any incoming activity messages (inbox concept).

## Flow

1. Create a policy for a kettle device
2. Create a digital twin (thing) for the kettle
3. Create a connection for device communication
4. App sets desired temperature (Outbox action)
5. Device reports temperature (Telemetry/Inbox action)
6. Device sends activity event (Event/Inbox action)
7. Polling thing's state multiple times

This shows the complete inbox-outbox flow pattern.
"""

import os
import sys
import time

from utils.ditto_operations import (
    cleanup,
    create_connection,
    create_policy,
    create_thing,
    get_thing,
    print_error,
    print_info,
    print_section,
    print_success,
    run_operations,
    update_thing_property,
)


def main():
    """Main entry point for Inbox Outbox Flow example."""
    try:
        # Get configuration from environment variables
        kettle_id = os.getenv("KETTLE_001_ID")
        policy_id = os.getenv("KETTLE_001_POLICY_ID")

        if not kettle_id or not policy_id:
            print_error(
                "Missing required environment variables: KETTLE_001_ID or KETTLE_001_POLICY_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 5: Inbox Outbox Flow")
        print_info("This example demonstrates the complete inbox-outbox flow pattern")
        print_info(f"Using kettle ID: {kettle_id}")
        print_info(f"Using policy ID: {policy_id}")
        print_info(
            "This simulates a smart kettle with temperature control and activity monitoring"
        )

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the operations to run
        operations = [
            ("Creating Policy", create_policy, policy_id, "policy.json", current_dir),
            ("Creating Thing", create_thing, kettle_id, "thing.json", current_dir),
            ("Creating Connection", create_connection, "connection.json", current_dir),
            (
                "App sets desired temperature (Outbox action)",
                update_thing_property,
                kettle_id,
                "features/temperature/properties/desired",
                95,
            ),
            (
                "Device reports temperature (Telemetry/Inbox action)",
                update_thing_property,
                kettle_id,
                "features/temperature/properties/value",
                92.5,
            ),
            (
                "Device sends activity event (Event/Inbox action)",
                update_thing_property,
                kettle_id,
                "features/activityLog/properties/lastEvent",
                "Boiling started",
            ),
        ]

        # Run all operations
        success = run_operations(operations)

        if not success:
            sys.exit(1)

        # Polling Thing's State (5 times, 2s interval)
        print_section("Polling Thing's State (5 times, 2s interval)")
        print_info("Simulating application polling the digital twin for updates")

        for i in range(1, 6):
            print_info(f"--- Poll #{i} ---")
            if not get_thing(kettle_id):
                print_error(f"Failed to retrieve thing state on poll #{i}")
                sys.exit(1)
            if i < 5:  # Don't sleep after the last poll
                print_info("Waiting 2 seconds before next poll...")
                time.sleep(2)

        print_section("Example 5 completed successfully!")
        print_success("Inbox-outbox flow example completed")
        print_info(
            "The smart kettle digital twin was successfully created and monitored"
        )
        print_info(
            "This demonstrates bidirectional communication between apps and devices"
        )

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 5: {e}")
        sys.exit(1)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
