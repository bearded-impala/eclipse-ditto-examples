#!/usr/bin/env python3
"""
Simple cleanup script for Eclipse Ditto.

This script directly calls the cleanup function without confirmation prompts.
Use this for automated cleanup or when you're sure you want to clean up.
"""

import os
import sys

import httpx
from tqdm import tqdm

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
        print_info("🧹 Starting Ditto cleanup...")

        # Create HTTP session
        session = httpx.Client(timeout=30.0)

        # 1. Delete all things (paginated) with progress bar
        print_section("Deleting All Things")
        print_info("📦 Deleting all things...")

        # Determine total number of things for progress bar (if available)
        total_things = None
        count_url = f"{DITTO_URL}/search/things/count"
        try:
            count_resp = session.get(count_url, auth=(AUTH_USER, AUTH_PASS))
            if count_resp.status_code == 200:
                text = count_resp.text.strip()
                digits = "".join(ch for ch in text if ch.isdigit())
                total_things = int(digits) if digits else None
        except Exception:
            total_things = None

        page_size = 200
        search_url = f"{DITTO_URL}/search/things"

        # Run async deletion with bounded concurrency
        import asyncio

        async def _delete_all_things_async() -> tuple[int, int]:
            max_concurrent = int(os.getenv("DITTO_CLEANUP_CONCURRENCY", "50"))
            semaphore = asyncio.Semaphore(max_concurrent)
            deleted = 0
            failed = 0
            cursor = None
            from tqdm import tqdm

            pbar = tqdm(total=total_things, desc="Deleting things", unit="thing")
            async with httpx.AsyncClient(timeout=30.0) as aclient:

                async def delete_one(thing_id: str):
                    nonlocal deleted, failed
                    async with semaphore:
                        try:
                            resp = await aclient.delete(
                                f"{DITTO_URL}/things/{thing_id}",
                                auth=(AUTH_USER, AUTH_PASS),
                            )
                            if resp.status_code in (204, 404):
                                deleted += 1
                            else:
                                failed += 1
                        except Exception:
                            failed += 1
                        finally:
                            pbar.update(1)

                while True:
                    params = {"option": f"size({page_size})"}
                    if cursor:
                        params["option"] += f",cursor({cursor})"
                    resp = await aclient.get(
                        search_url, auth=(AUTH_USER, AUTH_PASS), params=params
                    )
                    if resp.status_code != 200:
                        break
                    data = resp.json()
                    items = data.get("items", [])
                    if not items:
                        break
                    # Dispatch deletions for this page
                    tasks = [
                        asyncio.create_task(delete_one(it.get("thingId")))
                        for it in items
                        if it.get("thingId")
                    ]
                    if tasks:
                        await asyncio.gather(*tasks)
                    cursor = data.get("cursor")
                    if not cursor:
                        break
            pbar.close()
            return deleted, failed

        deleted, failed = asyncio.run(_delete_all_things_async())
        print_success(f"Deleted things: {deleted}")
        if failed:
            print_error(f"Failed deletions: {failed}")

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
