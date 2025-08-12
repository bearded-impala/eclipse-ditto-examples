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

from utils.ditto_operations import ExampleRunner


class RemoteDeviceControlExample(ExampleRunner):
    """Example 2: Remote Device Control"""

    def __init__(self):
        super().__init__("Remote Device Control")
        self.light_id = os.getenv("LIGHT_001_ID")
        self.policy_id = os.getenv("LIGHT_001_POLICY_ID")

    def run(self):
        """Run the Remote Device Control example."""
        try:
            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Creating Thing", lambda: self.create_thing(self.light_id)),
                (
                    "Updating Desired State (onOff)",
                    lambda: self.update_thing_property(
                        self.light_id, "features/onOff/properties/status/desired", True
                    ),
                ),
                (
                    "Retrieving Digital Twin State",
                    lambda: self.get_thing(self.light_id),
                ),
            ]

            if not self.run_operations(operations):
                return False

            self.log_section("Example 2 completed!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with RemoteDeviceControlExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
