#!/usr/bin/env python3
"""
Example: Using AWS Cognito JWT with Ditto API

Authenticates with Cognito, decodes the JWT sub claim, injects it as the policy
subject, then creates a policy and thing using the ID token as a bearer token.

Prerequisites:
- Gateway configured for the Cognito issuer (see README.md)
- COGNITO_USERNAME, COGNITO_PASSWORD, COGNITO_APP_CLIENT_ID set in .env
"""

import asyncio
import base64
import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

from utils.ditto_operations import create_policy, create_thing, get_thing

load_dotenv(Path(__file__).parent.parent.parent / ".env")

_COGNITO_USERNAME = os.getenv("COGNITO_USERNAME", "")
_COGNITO_PASSWORD = os.getenv("COGNITO_PASSWORD", "")
_COGNITO_APP_CLIENT_ID = os.getenv("COGNITO_APP_CLIENT_ID", "")
_COGNITO_REGION = os.getenv("COGNITO_REGION", "us-east-1")

_NAMESPACE = os.getenv("DITTO_NAMESPACE", "org.eclipse.ditto")
_POLICY_ID = f"{_NAMESPACE}:sensor-policy-cognito"
_THING_ID = f"{_NAMESPACE}:sensor-cognito-001"


def get_cognito_jwt_token() -> str:
    """Authenticate with AWS Cognito and return the ID token."""
    response = httpx.post(
        url=f"https://cognito-idp.{_COGNITO_REGION}.amazonaws.com/",
        headers={
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        },
        json={
            "AuthParameters": {
                "USERNAME": _COGNITO_USERNAME,
                "PASSWORD": _COGNITO_PASSWORD,
            },
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": _COGNITO_APP_CLIENT_ID,
        },
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json()["AuthenticationResult"]["IdToken"]


def decode_jwt_sub(token: str) -> str:
    """Decode the sub claim from a JWT token payload."""
    segment = token.split(".")[1]
    padding = "=" * (-len(segment) % 4)
    payload = json.loads(base64.urlsafe_b64decode(segment + padding))
    return str(payload["sub"])


async def main() -> None:
    missing = [v for v in ("COGNITO_USERNAME", "COGNITO_PASSWORD", "COGNITO_APP_CLIENT_ID") if not os.getenv(v)]
    if missing:
        print(f"Missing env vars: {', '.join(missing)}", file=sys.stderr)
        print("Set them in .env and run: uv run poe e9-cognito", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print("AWS Cognito JWT Authentication Example with Ditto API")
    print("=" * 60)
    print()

    print(f"Authenticating as {_COGNITO_USERNAME}...")
    jwt_token = get_cognito_jwt_token()
    jwt_sub = decode_jwt_sub(jwt_token)
    print(f"  sub claim:      {jwt_sub}")
    print(f"  policy subject: cognito:{jwt_sub}\n")

    example_dir = Path(__file__).parent

    # Inject the authenticated user's sub into the base policy
    policy_data = json.loads((example_dir / "policy-cognito.json").read_text())
    policy_data["entries"]["applicationPermissions"]["subjects"][f"cognito:{jwt_sub}"] = {
        "type": "AWS Cognito JWT subject"
    }
    temp_policy = example_dir / "temp_policy_cognito.json"
    temp_policy.write_text(json.dumps(policy_data, indent=2))

    temp_thing = example_dir / "temp_thing_cognito.json"
    thing_data = {
        "policyId": _POLICY_ID,
        "attributes": {
            "manufacturer": "Cognito JWT Demo",
            "model": "Cognito Authenticated Thing",
            "auth_method": "cognito",
        },
        "features": {
            "temperature": {"properties": {"value": 24.5}},
            "humidity": {"properties": {"value": 65.0}},
        },
    }
    temp_thing.write_text(json.dumps(thing_data, indent=2))

    try:
        print("1. Creating policy...")
        if not await create_policy(_POLICY_ID, temp_policy.name, str(example_dir), token=jwt_token):
            sys.exit(1)
        print(f"   Policy: {_POLICY_ID}\n")

        print("2. Creating thing...")
        if not await create_thing(_THING_ID, temp_thing.name, str(example_dir), token=jwt_token):
            sys.exit(1)
        print(f"   Thing: {_THING_ID}\n")

        print("3. Retrieving thing...")
        if not await get_thing(_THING_ID, token=jwt_token):
            sys.exit(1)
    finally:
        temp_policy.unlink(missing_ok=True)
        temp_thing.unlink(missing_ok=True)

    print("\nAll Cognito JWT examples completed successfully.")


if __name__ == "__main__":
    asyncio.run(main())
