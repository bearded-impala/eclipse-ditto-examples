#!/usr/bin/env python3
"""
Example 10: Direct gateway access with two auth methods.
"""

import asyncio
import sys
from pathlib import Path

from utils.ditto_operations import (
    DITTO_API_BASE,
    JWT_ISSUER,
    JWT_SUBJECT,
    PRE_AUTH_SUBJECT,
    _get_jwt_token,
    create_policy,
    create_thing,
    get_thing,
    print_error,
    print_info,
    print_section,
    print_success,
)

_POLICY_ID = "org.eclipse.ditto:sensor-direct-policy"
_THING_ID = "org.eclipse.ditto:sensor-direct-001"


async def main() -> None:
    print_section("Example 10: Direct gateway access (pre-auth header + external JWT)")
    print_info(f"Gateway base URL : {DITTO_API_BASE}")
    print_info(f"Pre-auth subject : {PRE_AUTH_SUBJECT}")
    print_info(f"JWT issuer       : {JWT_ISSUER} (subject '{JWT_SUBJECT}')")
    print()

    example_dir = str(Path(__file__).parent)

    print_section("Step 1: Create policy & thing using the pre-auth header")
    if not await create_policy(_POLICY_ID, "policy.json", example_dir):
        print_error("Failed to create policy")
        sys.exit(1)
    print_success(f"Policy created: {_POLICY_ID}")

    if not await create_thing(_THING_ID, "thing.json", example_dir):
        print_error("Failed to create thing")
        sys.exit(1)
    print_success(f"Thing created: {_THING_ID}")
    print()

    print_section("Step 2: Retrieve the thing using an external JWT bearer token")
    jwt_token = _get_jwt_token(JWT_ISSUER, JWT_SUBJECT)
    if not jwt_token:
        print_error("Could not obtain a JWT from the mock OAuth server")
        sys.exit(1)
    print_success(f"Got JWT (len={len(jwt_token)}) from issuer '{JWT_ISSUER}'")

    thing = await get_thing(_THING_ID, token=jwt_token)
    if not thing:
        print_error("Failed to retrieve thing with JWT")
        sys.exit(1)
    print_section("Example 10 completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
