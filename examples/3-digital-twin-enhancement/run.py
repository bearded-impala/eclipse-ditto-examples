#!/usr/bin/env python3
"""
Example 3: Digital Twin Enhancement

## Goal

Enrich a digital twin with external data (e.g., weather information based on location). This typically involves an external service fetching data and Ditto pushing it into the twin.

## Flow

1. Create a policy for a vehicle device
2. Create a digital twin (thing) for the vehicle
3. Simulate external service updating weather data
4. Retrieve the enhanced digital twin state

This shows how to enhance digital twins with external data sources.
"""

import os
import sys
from datetime import datetime

from utils.ditto_operations import ExampleRunner


class DigitalTwinEnhancementExample(ExampleRunner):
    """Example 3: Digital Twin Enhancement"""

    def __init__(self):
        super().__init__("Digital Twin Enhancement")
        self.vehicle_id = os.getenv("VEHICLE_001_ID")
        self.policy_id = os.getenv("VEHICLE_001_POLICY_ID")

    def run(self):
        """Run the Digital Twin Enhancement example."""
        try:
            weather_data = {
                "temperature": 18.2,
                "conditions": "Cloudy",
                "windSpeed": 15,
                "lastUpdated": "2025-07-22T09:15:00Z",
            }

            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Creating Thing", lambda: self.create_thing(self.vehicle_id)),
                (
                    "Simulating External Service (Update Weather Data)",
                    lambda: self.update_thing_property(
                        self.vehicle_id, "features/weather/properties", weather_data
                    ),
                ),
                (
                    "Retrieving Digital Twin State",
                    lambda: self.get_thing(self.vehicle_id),
                ),
            ]

            if not self.run_operations(operations):
                return False

            self.log_section("Example 3 completed!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with DigitalTwinEnhancementExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
