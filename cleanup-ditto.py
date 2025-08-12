#!/usr/bin/env python3
"""
Cleanup script for Eclipse Ditto.

This script deletes all things, policies, and connections from Ditto.
Use this to clean up the Ditto instance after running examples.
"""

import os
import sys

from dotenv import load_dotenv

from utils.config import Config
from utils.http_client import DittoClient
from utils.logging_utils import setup_basic_logging


def cleanup_ditto():
    """Clean up all things, policies, and connections from Ditto."""
    logger = setup_basic_logging()

    try:
        # Load environment variables
        logger.info("Loading environment variables...")
        load_dotenv()

        # Setup HTTP client
        config = Config.load()
        client = DittoClient(config)

        logger.info("🧹 Starting Ditto cleanup...")

        # 1. Delete all things
        logger.info("📦 Deleting all things...")
        thing_ids = client.list_thing_ids()
        if thing_ids:
            logger.info(f"Found {len(thing_ids)} things to delete")
            for thing_id in thing_ids:
                if client.delete_thing(thing_id):
                    logger.info(f"✅ Deleted thing: {thing_id}")
                else:
                    logger.warning(f"⚠️ Failed to delete thing: {thing_id}")
        else:
            logger.info("No things found to delete")

        # 2. Delete all policies
        logger.info("🔐 Deleting all policies...")
        # Note: We need to get policy IDs first
        # For now, we'll delete the known policies from our examples
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
                url = f"{os.getenv('DITTO_POLICIES_API')}/{policy_id}"
                try:
                    response = client.session.delete(url, auth=client.auth, timeout=10)
                    if response.status_code in (204, 404):
                        logger.info(f"✅ Deleted policy: {policy_id}")
                    else:
                        logger.warning(
                            f"⚠️ Failed to delete policy {policy_id} (HTTP {response.status_code})"
                        )
                except Exception as e:
                    logger.warning(f"⚠️ Error deleting policy {policy_id}: {e}")

        # 3. Delete all connections
        logger.info("🔗 Deleting all connections...")
        # Since we can't easily list all connections, we'll delete known ones
        # and also try to delete any connections that might exist
        known_connection_ids = [
            "mqtt-connection-source",
            "mqtt-connection-target",
            "ditto-to-mosquitto-event-bridge",
            "amqp-connection",
            "kafka-connection",
        ]

        connections_url = f"{os.getenv('DITTO_DEVOPS_API')}/piggyback/connectivity"

        # Try to delete known connections
        for connection_id in known_connection_ids:
            delete_url = f"{connections_url}/{connection_id}"
            try:
                delete_response = client.session.delete(
                    delete_url,
                    auth=(
                        os.getenv("DITTO_DEVOPS_USERNAME"),
                        os.getenv("DITTO_DEVOPS_PASSWORD"),
                    ),
                    timeout=10,
                )
                if delete_response.status_code in (204, 404):
                    logger.info(f"✅ Deleted connection: {connection_id}")
                else:
                    logger.debug(
                        f"Connection {connection_id} not found or already deleted"
                    )
            except Exception as e:
                logger.debug(f"Error deleting connection {connection_id}: {e}")

        # Also try to get connections if the API supports it
        # Use the correct connections endpoint
        connection_endpoints = [f"{os.getenv('DITTO_API_BASE')}/connections"]

        for endpoint in connection_endpoints:
            try:
                response = client.session.get(
                    endpoint,
                    auth=client.auth,  # Use regular Ditto auth for api/2/connections
                    timeout=10,
                )

                if response.status_code == 200:
                    connections = response.json()
                    if isinstance(connections, list):
                        for connection in connections:
                            connection_id = connection.get("id")
                            if (
                                connection_id
                                and connection_id not in known_connection_ids
                            ):
                                # Try different deletion methods
                                deleted = False

                                # Method 1: Try DELETE request on the correct endpoint
                                delete_urls = [
                                    f"{os.getenv('DITTO_API_BASE')}/connections/{connection_id}"
                                ]

                                for delete_url in delete_urls:
                                    try:
                                        delete_response = client.session.delete(
                                            delete_url,
                                            auth=client.auth,  # Use regular Ditto auth for api/2/connections
                                            timeout=10,
                                        )
                                        if delete_response.status_code in (204, 404):
                                            logger.info(
                                                f"✅ Deleted connection: {connection_id}"
                                            )
                                            deleted = True
                                            break
                                        else:
                                            logger.debug(
                                                f"Failed to delete connection {connection_id} from {delete_url} (HTTP {delete_response.status_code})"
                                            )
                                    except Exception as e:
                                        logger.debug(
                                            f"Error deleting connection {connection_id} from {delete_url}: {e}"
                                        )

                                # Method 2: Try POST with delete command as fallback
                                if not deleted:
                                    try:
                                        delete_command = {
                                            "targetActorSelection": "/system/sharding/connection",
                                            "headers": {"aggregate": False},
                                            "piggybackCommand": {
                                                "type": "connectivity.commands:deleteConnection",
                                                "connectionId": connection_id,
                                            },
                                        }

                                        delete_response = client.session.post(
                                            connections_url,
                                            json=delete_command,
                                            auth=(
                                                os.getenv("DITTO_DEVOPS_USERNAME"),
                                                os.getenv("DITTO_DEVOPS_PASSWORD"),
                                            ),
                                            timeout=10,
                                        )
                                        if delete_response.status_code in (
                                            200,
                                            204,
                                            404,
                                        ):
                                            logger.info(
                                                f"✅ Deleted connection: {connection_id}"
                                            )
                                            deleted = True
                                        else:
                                            logger.debug(
                                                f"Failed to delete connection {connection_id} via POST command (HTTP {delete_response.status_code})"
                                            )
                                    except Exception as e:
                                        logger.debug(
                                            f"Error deleting connection {connection_id} via POST command: {e}"
                                        )

                                if not deleted:
                                    logger.warning(
                                        f"⚠️ Could not delete connection {connection_id} using any method"
                                    )
                    break  # If we found a working endpoint, stop trying others
                else:
                    logger.debug(
                        f"Could not list connections from {endpoint} (HTTP {response.status_code})"
                    )
            except Exception as e:
                logger.debug(f"Could not list connections from {endpoint}: {e}")
        else:
            logger.debug(
                "Could not list connections from any endpoint - this is normal for some Ditto versions"
            )

        logger.info("✅ Ditto cleanup completed!")
        return True

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        return False
    finally:
        if "client" in locals():
            client.close()


def main():
    """Main entry point."""
    print("🧹 Ditto Cleanup Script")
    print("This will delete ALL things, policies, and connections from Ditto.")
    print()

    # Ask for confirmation
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() not in ["yes", "y"]:
        print("Cleanup cancelled.")
        sys.exit(0)

    success = cleanup_ditto()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
