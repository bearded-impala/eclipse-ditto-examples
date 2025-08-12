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

import sys
import time
import os
from utils.ditto_operations import ExampleRunner


class InboxOutboxFlowExample(ExampleRunner):
    """Example 5: Inbox Outbox Flow"""
    
    def __init__(self):
        super().__init__("Inbox Outbox Flow")
        self.kettle_id = os.getenv("KETTLE_001_ID")
        self.policy_id = os.getenv("KETTLE_001_POLICY_ID")
    
    def create_connection(self) -> bool:
        """Create a connection for device communication."""
        try:
            connection_data = self.load_json_file("connection.json")
            
            # Use devops auth and the correct endpoint
            url = f"{os.getenv('DITTO_API_BASE')}/connections"
            headers = {"Content-Type": "application/json"}
            auth = (os.getenv("DITTO_DEVOPS_USERNAME"), os.getenv("DITTO_DEVOPS_PASSWORD"))
            
            response = self.client.session.post(
                url,
                json=connection_data,
                auth=auth,
                headers=headers,
                timeout=30
            )
            
            if 200 <= response.status_code < 300:
                self.logger.info("✅ Connection created")
                return True
            else:
                self.logger.error(f"❌ Failed to create connection (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.logger.error(f"❌ Error creating connection: {e}")
            return False
    
    def run(self):
        """Run the Inbox Outbox Flow example."""
        try:
            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Creating Thing", lambda: self.create_thing(self.kettle_id)),
                ("Creating Connection", lambda: self.create_connection()),
                ("App sets desired temperature (Outbox action)", 
                 lambda: self.update_thing_property(self.kettle_id, "features/temperature/properties/desired", 95)),
                ("Device reports temperature (Telemetry/Inbox action)", 
                 lambda: self.update_thing_property(self.kettle_id, "features/temperature/properties/value", 92.5)),
                ("Device sends activity event (Event/Inbox action)", 
                 lambda: self.update_thing_property(self.kettle_id, "features/activityLog/properties/lastEvent", "Boiling started")),
            ]
            
            if not self.run_operations(operations):
                return False
            
            # Polling Thing's State (5 times, 2s interval)
            self.log_section("Polling Thing's State (5 times, 2s interval)")
            for i in range(1, 6):
                self.logger.info(f"--- Poll #{i} ---")
                if not self.get_thing(self.kettle_id):
                    return False
                if i < 5:  # Don't sleep after the last poll
                    time.sleep(2)
            
            self.log_section("Example 5 completed!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with InboxOutboxFlowExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
