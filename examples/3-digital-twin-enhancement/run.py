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

import asyncio
import os
import sys

from utils.ditto_operations import (
    create_policy,
    create_thing,
    get_thing,
    print_error,
    print_info,
    print_section,
    print_success,
    update_thing_property,
)


async def main():
    """Main entry point for Digital Twin Enhancement example."""
    try:
        # Get configuration from environment variables
        vehicle_id = os.getenv("VEHICLE_001_ID")
        policy_id = os.getenv("VEHICLE_001_POLICY_ID")

        if not vehicle_id or not policy_id:
            print_error(
                "Missing required environment variables: VEHICLE_001_ID or VEHICLE_001_POLICY_ID"
            )
            print_info("Please check your .env file or environment variables")
            sys.exit(1)

        print_section("Example 3: Digital Twin Enhancement")
        print_info(
            "This example demonstrates enriching digital twins with external data"
        )
        print_info(f"Using vehicle ID: {vehicle_id}")
        print_info(f"Using policy ID: {policy_id}")

        # Simulate weather data from external service
        weather_data = {
            "temperature": 18.2,
            "conditions": "Cloudy",
            "windSpeed": 15,
            "lastUpdated": "2025-07-22T09:15:00Z",
        }

        print_info("Simulating external weather service data:")
        print_info(f"  Temperature: {weather_data['temperature']}°C")
        print_info(f"  Conditions: {weather_data['conditions']}")
        print_info(f"  Wind Speed: {weather_data['windSpeed']} km/h")

        # Get current directory for file operations
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Step 1: Create Policy
        if not await create_policy(policy_id, "policy.json", current_dir):
            print_error("Failed to create policy")
            sys.exit(1)

        # Step 2: Create Thing
        if not await create_thing(vehicle_id, "thing.json", current_dir):
            print_error("Failed to create thing")
            sys.exit(1)

        # Step 3: Simulate External Service (Update Weather Data)
        if not await update_thing_property(
            vehicle_id, "features/weather/properties", weather_data
        ):
            print_error("Failed to update weather data")
            sys.exit(1)

        # Step 4: Retrieve Digital Twin State
        if not await get_thing(vehicle_id):
            print_error("Failed to retrieve thing")
            sys.exit(1)

        print_section("Example 3 completed successfully!")
        print_success("Digital twin enhancement example completed")
        print_info("The vehicle's digital twin was enriched with weather data")
        print_info(
            "This demonstrates how external services can enhance digital twins"
        )

    except KeyboardInterrupt:
        print_error("Example interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error in Example 3: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
