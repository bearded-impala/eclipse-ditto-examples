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

import sys
import os
from utils.ditto_operations import ExampleRunner


class OutboxPatternExample(ExampleRunner):
    """Example 4: Outbox Pattern"""
    
    def __init__(self):
        super().__init__("Outbox Pattern")
        self.doorlock_id = os.getenv("DOORLOCK_001_ID")
        self.policy_id = os.getenv("DOORLOCK_001_POLICY_ID")
    
    def run(self):
        """Run the Outbox Pattern example."""
        try:
            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Creating Thing", lambda: self.create_thing(self.doorlock_id)),
                ("Application issues command (sets desired state - Outbox)", 
                 lambda: self.update_thing_property(self.doorlock_id, "features/lockState/properties/status/desired", "LOCKED")),
                ("Simulate Device Action and Report (Completing the Outbox cycle)", 
                 lambda: self.update_thing_property(self.doorlock_id, "features/lockState/properties/status/value", "LOCKED")),
                ("Retrieving Digital Twin State", lambda: self.get_thing(self.doorlock_id)),
            ]
            
            if not self.run_operations(operations):
                return False
            
            self.log_section("Example 4 completed!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with OutboxPatternExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
