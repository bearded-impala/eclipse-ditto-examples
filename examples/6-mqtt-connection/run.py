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

import asyncio
import os
import subprocess
import sys
import time

from utils.ditto_operations import (
    create_policy,
    create_thing,
    create_connection_piggyback,
    print_error,
    print_info,
    print_section,
    print_success,
)


def start_mqtt_broker() -> bool:
    """Start the MQTT broker."""
    try:
        print_section("Starting MQTT Broker")
        print_info("🚀 Starting MQTT broker...")

        subprocess.run(
            ["uv", "run", "poe", "start-mqtt-broker"],
            capture_output=True,
            text=True,
            check=True,
        )
        print_success("MQTT broker started")

        # Wait for broker to be ready
        print_info("⏳ Waiting for MQTT broker to be ready...")
        time.sleep(3)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to start MQTT broker: {e}")
        return False


async def main():
    """Main entry point for MQTT Connection example."""
    try:
        # Get configuration from environment variables
        sensor01_id = os.getenv("SENSOR01_ID")
        sensor02_id = os.getenv("SENSOR02_ID")
        policy_id = os.getenv("TEST_POLICY_ID")
        mqtt_topic_prefix = os.getenv("MQTT_TOPIC_PREFIX")

        if not all([sensor01_id, sensor02_id, policy_id, mqtt_topic_prefix]):
            print_error(
                "Missing required environment variables: SENSOR01_ID, SENSOR02_ID, TEST_POLICY_ID, or MQTT_TOPIC_PREFIX"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 6: MQTT Connection")
        print_info("This example demonstrates connecting devices to Ditto via MQTT")
        print_info(f"Using sensor01 ID: {sensor01_id}")
        print_info(f"Using sensor02 ID: {sensor02_id}")
        print_info(f"Using policy ID: {policy_id}")
        print_info(f"Using MQTT topic prefix: {mqtt_topic_prefix}")

        # Step 1: Start MQTT Broker
        if not start_mqtt_broker():
            print_error("Failed to start MQTT broker")
            sys.exit(1)

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 2: Create Ditto policy
        if not await create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 3: Create Ditto things
        if not await create_thing(sensor01_id, "sensor01.json", current_dir):
            print_error("Failed to create sensor01")
            sys.exit(1)
        
        if not await create_thing(sensor02_id, "sensor02.json", current_dir):
            print_error("Failed to create sensor02")
            sys.exit(1)

        # Step 4: Create MQTT connections
        if not await create_connection_piggyback("connection_source.json", current_dir):
            print_error("Failed to create MQTT source connection")
            sys.exit(1)
        
        if not await create_connection_piggyback("connection_target.json", current_dir):
            print_error("Failed to create MQTT target connection")
            sys.exit(1)

        # Setup Complete
        print_section("Setup Complete!")
        print_success("MQTT connection setup completed successfully")

        # Print test instructions
        print_info("🧪 To test:")
        print_info("")
        print_info("🦟 bash into mosquitto container")
        print_info("  docker exec -it mosquitto-broker /bin/sh")
        print_info("")
        print_info("📤 Publish an update:")
        print_info(
            f'  mosquitto_pub -h host.docker.internal -t {mqtt_topic_prefix}/sensor01 -m \'{{"temperature": 56, "humidity": 86, "thingId": "{sensor01_id}"}}\''
        )
        print_info("")
        print_info("🧹 When done testing, clean up with:")
        print_info("  uv run poe stop-mqtt-broker")
        print_info("  uv run poe cleanup")

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 6: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
