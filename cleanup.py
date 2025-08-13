#!/usr/bin/env python3
"""
Simple cleanup script for Eclipse Ditto.

This script directly calls the cleanup function without confirmation prompts.
Use this for automated cleanup or when you're sure you want to clean up.
"""

import json
import os
import sys

import httpx
from dotenv import load_dotenv

from utils.ditto_operations import (
    AUTH_PASS,
    AUTH_USER,
    DITTO_URL,
    print_error,
    print_info,
    print_section,
    print_success,
)


def cleanup_ditto():
    """Clean up all things, policies, and connections from Ditto."""
    try:
        print_section("Ditto Cleanup")
        print_info("🧹 Starting Ditto cleanup...")

        # Create HTTP session
        session = httpx.Client(timeout=30.0)

        # 1. Delete all things
        print_section("Deleting All Things")
        print_info("📦 Deleting all things...")

        # Get all things
        search_url = f"{DITTO_URL}/search/things"
        response = session.get(
            search_url, auth=(AUTH_USER, AUTH_PASS), params={"option": "size(200)"}
        )

        if response.status_code == 200:
            data = response.json()
            things = data.get("items", [])
            print_info(f"Found {len(things)} things to delete")

            for thing in things:
                thing_id = thing.get("thingId")
                if thing_id:
                    delete_url = f"{DITTO_URL}/things/{thing_id}"
                    delete_response = session.delete(
                        delete_url, auth=(AUTH_USER, AUTH_PASS)
                    )
                    if delete_response.status_code in (204, 404):
                        print_success(f"Deleted thing: {thing_id}")
                    else:
                        print_error(f"Failed to delete thing: {thing_id}")
        else:
            print_info("No things found to delete")

        # 2. Delete known policies
        print_section("Deleting Known Policies")
        print_info("🔐 Deleting known policies...")

        known_policies = [
            os.getenv("SENSOR_001_POLICY_ID"),
            os.getenv("LIGHT_001_POLICY_ID"),
            os.getenv("VEHICLE_001_POLICY_ID"),
            os.getenv("DOORLOCK_001_POLICY_ID"),
            os.getenv("KETTLE_001_POLICY_ID"),
            os.getenv("SENSOR_POLICY_ID"),
            os.getenv("TEST_POLICY_ID"),
        ]

        for policy_id in known_policies:
            if policy_id:
                delete_url = f"{DITTO_URL}/policies/{policy_id}"
                delete_response = session.delete(
                    delete_url, auth=(AUTH_USER, AUTH_PASS)
                )
                if delete_response.status_code in (204, 404):
                    print_success(f"Deleted policy: {policy_id}")
                else:
                    print_error(f"Failed to delete policy: {policy_id}")

        # 3. Delete known connections
        print_section("Deleting Known Connections")
        print_info("🔗 Deleting known connections...")

        # Use DevOps API for connections
        ditto_devops_url = os.getenv(
            "DITTO_DEVOPS_API", "http://localhost:8080/devops"
        ).rstrip("/")
        devops_user = os.getenv("DITTO_DEVOPS_USERNAME", "devops")
        devops_pass = os.getenv("DITTO_DEVOPS_PASSWORD", "foobar")

        # Known connection IDs from examples
        known_connection_ids = [
            "mqtt-connection-source",
            "mqtt-connection-target",
            "ditto-to-mosquitto-event-bridge",
            "amqp-connection",
            "kafka-connection",
        ]

        for connection_id in known_connection_ids:
            # Delete connection using DevOps API
            delete_command = {
                "targetActorSelection": "/system/sharding/connection",
                "headers": {"aggregate": False},
                "piggybackCommand": {
                    "type": "connectivity.commands:deleteConnection",
                    "connectionId": connection_id,
                },
            }

            delete_url = f"{ditto_devops_url}/piggyback/connectivity"
            delete_response = session.post(
                delete_url,
                json=delete_command,
                auth=(devops_user, devops_pass),
                timeout=30,
            )

            if delete_response.status_code in (200, 204, 404):
                print_success(f"Deleted connection: {connection_id}")
            else:
                print_error(f"Failed to delete connection: {connection_id}")

        session.close()
        print_section("Cleanup Complete")
        print_success("✅ Ditto cleanup completed!")
        return True

    except Exception as e:
        print_error(f"❌ Error during cleanup: {e}")
        return False


def main():
    """Main entry point."""
    success = cleanup_ditto()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
