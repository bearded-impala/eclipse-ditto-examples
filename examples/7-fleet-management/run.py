#!/usr/bin/env python3
"""
Example 7: Fleet Management

This example demonstrates how to:
1. Create a policy for sensor devices
2. Bulk create multiple things from JSON files
3. Update sensor reported states
4. Search things with various filters
5. Combine search queries

This shows fleet management capabilities in Eclipse Ditto.
"""

import sys
import glob
import json
from pathlib import Path
import os
from utils.ditto_operations import ExampleRunner


class FleetManagementExample(ExampleRunner):
    """Example 7: Fleet Management"""
    
    def __init__(self):
        super().__init__("Fleet Management")
        self.policy_id = os.getenv("SENSOR_POLICY_ID")
        self.sensor002_id = os.getenv("SENSOR_002_ID")
        self.fleet_folder = self.script_dir / "fleet"
    
    def bulk_create_things(self) -> bool:
        """Bulk create things from JSON files in the fleet folder."""
        try:
            # Get all JSON files in the fleet folder
            json_files = glob.glob(str(self.fleet_folder / "*.json"))
            
            if not json_files:
                self.logger.error(f"❌ No JSON files found in {self.fleet_folder}")
                return False
            
            for json_file in sorted(json_files):
                try:
                    # Load the JSON data
                    thing_data = self.load_json_file(Path(json_file).name, str(self.fleet_folder))
                    thing_id = thing_data.get("thingId")
                    
                    if not thing_id:
                        self.logger.warning(f"❌ Skipping {json_file} - no 'thingId' found")
                        continue
                    
                    self.logger.info(f"📡 Uploading {thing_id} from {Path(json_file).name}...")
                    
                    # Create the thing
                    success = self.client.create_thing(thing_id, thing_data)
                    if success:
                        self.logger.info(f"✅ Done with {thing_id}")
                    else:
                        self.logger.error(f"❌ Failed to create {thing_id}")
                        return False
                    
                    self.logger.info("----------------------------")
                    
                except Exception as e:
                    self.logger.error(f"❌ Error processing {json_file}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in bulk create: {e}")
            return False
    
    def search_things(self, filter_expr: str = None, description: str = "all things") -> bool:
        """
        Search things with optional filter.
        
        Args:
            filter_expr: Optional filter expression
            description: Description of the search for logging
        """
        try:
            self.log_section(f"Search: {description}")
            results = self.client.search_things(filter_expr)
            
            if results:
                print(json.dumps(results, indent=2))
                return True
            else:
                self.logger.warning("No results found")
                return True
        except Exception as e:
            self.logger.error(f"❌ Error searching things: {e}")
            return False
    
    def run(self):
        """Run the Fleet Management example."""
        try:
            operations = [
                ("Creating Policy", lambda: self.create_policy(self.policy_id)),
                ("Bulk Creating Things", lambda: self.bulk_create_things()),
                ("Update sensor-002 reported state", 
                 lambda: self.update_thing_property(self.sensor002_id, "features/humidity/properties/value", 70.1)),
            ]
            
            if not self.run_operations(operations):
                return False
            
            # Search operations
            search_operations = [
                ("Find all things", lambda: self.search_things(description="Find all things")),
                ("Find all things with manufacturer: 'ABC'", 
                 lambda: self.search_things(filter_expr="eq(attributes/manufacturer,'ABC')", description="Find all things with manufacturer: 'ABC'")),
                ("Find all things where temperature > 20 Celsius", 
                 lambda: self.search_things(filter_expr="gt(features/temperature/properties/value,20)", description="Find all things where temperature > 20 Celsius")),
                ("Find all things in the 'Living Room'", 
                 lambda: self.search_things(filter_expr="eq(attributes/location,'Living Room')", description="Find all things in the 'Living Room'")),
                ("Combine queries (temperature > 20 AND location = 'Living Room')", 
                 lambda: self.search_things(filter_expr="and(gt(features/temperature/properties/value,20),eq(attributes/location,'Living Room'))", description="Combine queries (temperature > 20 AND location = 'Living Room')")),
            ]
            
            if not self.run_operations(search_operations):
                return False
            
            self.log_section("Example 7 completed!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with FleetManagementExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
