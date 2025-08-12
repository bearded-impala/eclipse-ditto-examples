#!/usr/bin/env python3
"""
Example 6: MQTT Connection

## Goal

Connect a device to Ditto via MQTT.

## Flow

1. Start an MQTT broker
2. Create Ditto policies and things
3. Create MQTT source and target connections
4. Set up device communication via MQTT

This shows how to connect devices to Ditto via MQTT.
"""

import os
import subprocess
import sys
import time

from utils.ditto_operations import ExampleRunner


class MQTTConnectionExample(ExampleRunner):
    """Example 6: MQTT Connection"""

    def __init__(self):
        super().__init__("MQTT Connection")
        self.sensor01_id = os.getenv("SENSOR01_ID")
        self.sensor02_id = os.getenv("SENSOR02_ID")
        self.policy_id = os.getenv("TEST_POLICY_ID")
        self.mqtt_topic_prefix = os.getenv("MQTT_TOPIC_PREFIX")
        self.connection_timeout = os.getenv("CONNECTION_TIMEOUT", "60")

    def cleanup(self):
        """Override cleanup to not remove MQTT broker - let user clean up manually."""
        # Don't clean up automatically - let the user test the MQTT functionality
        # and clean up manually when done
        pass

    def start_mqtt_broker(self) -> bool:
        """Start the MQTT broker."""
        try:
            self.logger.info("🚀 Starting MQTT broker...")
            subprocess.run(
                ["uv", "run", "poe", "start-mqtt-broker"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.logger.info("✅ MQTT broker started")

            # Wait for broker to be ready
            self.logger.info("⏳ Waiting for MQTT broker to be ready...")
            time.sleep(3)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ Failed to start MQTT broker: {e}")
            return False

    def create_thing_from_file(self, thing_id: str, filename: str) -> bool:
        """Create a thing from a JSON file."""
        try:
            thing_data = self.load_json_file(filename)
            success = self.client.create_thing(thing_id, thing_data)
            if success:
                self.logger.info(f"✅ Thing created: {thing_id}")
            else:
                self.logger.error(f"❌ Failed to create thing: {thing_id}")
            return success
        except Exception as e:
            self.logger.error(f"❌ Error creating thing {thing_id}: {e}")
            return False

    def create_connection_from_file(self, filename: str, connection_type: str) -> bool:
        """Create a connection from a JSON file."""
        try:
            connection_data = self.load_json_file(filename)

            # Use devops API for connections
            url = f"{os.getenv('DITTO_DEVOPS_API')}/piggyback/connectivity?timeout={self.connection_timeout}"
            headers = {"Content-Type": "application/json"}
            auth = (
                os.getenv("DITTO_DEVOPS_USERNAME"),
                os.getenv("DITTO_DEVOPS_PASSWORD"),
            )

            response = self.client.session.post(
                url, json=connection_data, auth=auth, headers=headers, timeout=30
            )

            if 200 <= response.status_code < 300:
                self.logger.info(f"✅ {connection_type} connection created")
                return True
            else:
                self.logger.error(
                    f"❌ Failed to create {connection_type} connection (HTTP {response.status_code})"
                )
                return False
        except Exception as e:
            self.logger.error(f"❌ Error creating {connection_type} connection: {e}")
            return False

    def run(self):
        """Run the MQTT Connection example."""
        try:
            # Start MQTT Broker
            if not self.start_mqtt_broker():
                return False

            operations = [
                ("Creating Ditto policy", lambda: self.create_policy(self.policy_id)),
                (
                    "Creating Ditto things",
                    lambda: self.create_thing_from_file(
                        self.sensor01_id, "sensor01.json"
                    )
                    and self.create_thing_from_file(self.sensor02_id, "sensor02.json"),
                ),
                (
                    "Creating MQTT connections",
                    lambda: self.create_connection_from_file(
                        "connection_source.json", "MQTT source"
                    )
                    and self.create_connection_from_file(
                        "connection_target.json", "MQTT target"
                    ),
                ),
            ]

            if not self.run_operations(operations):
                return False

            # Setup Complete
            self.log_section("Setup Complete!")

            # Print test instructions
            print(f"""
🧪 To test:

🦟 bash into mosquitto container
  docker exec -it mosquitto-broker /bin/sh

📤 Publish an update:
  mosquitto_pub -h host.docker.internal -t {self.mqtt_topic_prefix}/sensor01 -m '{{"temperature": 56, "humidity": 86, "thingId": "{self.sensor01_id}"}}'

🧹 When done testing, clean up with:
  uv run poe stop-mqtt-broker
  uv run poe cleanup-ditto
""")

            return True

        except Exception as e:
            self.logger.error(f"❌ Error running example: {e}")
            return False


def main():
    """Main entry point."""
    with MQTTConnectionExample() as example:
        success = example.run()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
