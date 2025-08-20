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

from utils.ditto_operations import (
    cleanup,
    create_policy,
    create_thing,
    load_json_file,
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


def create_thing_from_file(thing_id: str, filename: str) -> bool:
    """Create a thing from a JSON file."""
    try:
        print_section(f"Creating Thing: {thing_id}")

        thing_data = load_json_file(filename)
        url = f"{os.getenv('DITTO_API_BASE', 'http://localhost:8080/api/2')}/things/{thing_id}"
        headers = {"Content-Type": "application/json"}
        auth = (
            os.getenv("DITTO_USERNAME", "ditto"),
            os.getenv("DITTO_PASSWORD", "ditto"),
        )

        import httpx

        session = httpx.Client(timeout=30.0)
        response = session.put(url, json=thing_data, auth=auth, headers=headers)

        if 200 <= response.status_code < 300:
            print_success(f"Thing created: {thing_id}")
            return True
        else:
            print_error(
                f"Failed to create thing {thing_id}. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error creating thing {thing_id}: {e}")
        return False


def create_connection_from_file(filename: str, connection_type: str) -> bool:
    """Create a connection from a JSON file."""
    try:
        print_section(f"Creating {connection_type} Connection")

        connection_data = load_json_file(filename)
        connection_timeout = os.getenv("CONNECTION_TIMEOUT", "60")

        # Use devops API for connections
        url = f"{os.getenv('DITTO_DEVOPS_API', 'http://localhost:8080/devops')}/piggyback/connectivity?timeout={connection_timeout}"
        headers = {"Content-Type": "application/json"}
        auth = (
            os.getenv("DITTO_DEVOPS_USERNAME", "devops"),
            os.getenv("DITTO_DEVOPS_PASSWORD", "foobar"),
        )

        import httpx

        session = httpx.Client(timeout=30.0)
        response = session.post(url, json=connection_data, auth=auth, headers=headers)

        if 200 <= response.status_code < 300:
            print_success(f"{connection_type} connection created")
            return True
        else:
            print_error(
                f"Failed to create {connection_type} connection. Status: {response.status_code}"
            )
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error creating {connection_type} connection: {e}")
        return False


def main():
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
        if not create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 3: Create Ditto things
        if not create_thing_from_file(sensor01_id, "sensor01.json"):
            print_error("Failed to create sensor01")
            sys.exit(1)
        
        if not create_thing_from_file(sensor02_id, "sensor02.json"):
            print_error("Failed to create sensor02")
            sys.exit(1)

        # Step 4: Create MQTT connections
        if not create_connection_from_file("connection_source.json", "MQTT source"):
            print_error("Failed to create MQTT source connection")
            sys.exit(1)
        
        if not create_connection_from_file("connection_target.json", "MQTT target"):
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
    finally:
        cleanup()


if __name__ == "__main__":
    main()
