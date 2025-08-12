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

from utils.ditto_operations import ExampleRunner


class DeviceStateSyncExample(ExampleRunner):
    """Example 1: Device State Sync"""

    def __init__(self):
        super().__init__("Device State Sync")
        self.sensor_id = os.getenv("SENSOR_001_ID")
        self.policy_id = os.getenv("SENSOR_001_POLICY_ID")

    def run(self):
        """Run the Device State Sync example."""
        try:
            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Creating Thing", lambda: self.create_thing(self.sensor_id)),
                (
                    "Updating Reported State (temperature)",
                    lambda: self.update_thing_property(
                        self.sensor_id, "features/temperature/properties/value", 22.8
                    ),
                ),
                (
                    "Retrieving Digital Twin State",
                    lambda: self.get_thing(self.sensor_id),
                ),
            ]

            if not self.run_operations(operations):
                return False

            self.log_section("Example 1 completed!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with DeviceStateSyncExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
