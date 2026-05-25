#!/usr/bin/env python3
"""
Example 10 / Variant B - External JWT bearer token, end-to-end.

Runs inside the docker network defined by `docker-compose-e10-jwt.yml` so
`gateway:8080` and `oauth:9900` both resolve.
"""

import json
import sys
from pathlib import Path
from typing import Any

import httpx

GATEWAY = "http://gateway:8080"
OAUTH_TOKEN_URL = "http://oauth:9900/ditto/token"

HERE = Path(__file__).parent
POLICY: dict[str, Any] = json.loads((HERE / "policy-jwt.json").read_text())
THING: dict[str, Any] = json.loads((HERE / "thing-jwt.json").read_text())
POLICY_ID: str = POLICY["policyId"]
THING_ID: str = THING["thingId"]


def banner(text: str) -> None:
    print(f"\n=== {text} ===")


def fetch_jwt() -> str:
    r = httpx.post(
        OAUTH_TOKEN_URL,
        data={
            "grant_type": "client_credentials",
            "client_id": "ditto",
            "client_secret": "secret",
            "scope": "openid",
        },
    )
    r.raise_for_status()
    return str(r.json()["access_token"])


def main() -> None:
    banner("1. Fetch JWT from the mock OAuth server")
    jwt = fetch_jwt()
    print(f"  Got token (len={len(jwt)}) from {OAUTH_TOKEN_URL}")

    bearer_headers: dict[str, str] = {"Authorization": f"Bearer {jwt}"}

    banner("2. /api/2 with Bearer <jwt> (expect SUCCESS)")
    r = httpx.put(
        f"{GATEWAY}/api/2/policies/{POLICY_ID}", json=POLICY, headers=bearer_headers
    )
    print(f"  PUT  /api/2/policies/{POLICY_ID}  -> {r.status_code}")
    r.raise_for_status()

    r = httpx.put(
        f"{GATEWAY}/api/2/things/{THING_ID}", json=THING, headers=bearer_headers
    )
    print(f"  PUT  /api/2/things/{THING_ID}  -> {r.status_code}")
    r.raise_for_status()

    r = httpx.get(f"{GATEWAY}/api/2/things/{THING_ID}", headers=bearer_headers)
    print(f"  GET  /api/2/things/{THING_ID}  -> {r.status_code}")
    r.raise_for_status()

    banner("3. /api/2 with HTTP Basic Auth direct to gateway (expect FAILURE)")
    r = httpx.get(f"{GATEWAY}/api/2/things/{THING_ID}", auth=("ditto", "ditto"))
    print(f"  GET  /api/2/things/{THING_ID}  -> {r.status_code}")
    if r.status_code == 200:
        print("  UNEXPECTED: Basic Auth was accepted on /api/2 by the gateway")
        sys.exit(1)
    print(
        "  Confirmed: the gateway has no native HTTP Basic Auth on /api/2."
        " In a normal stack, nginx terminates Basic and forwards as a pre-auth"
        " header."
    )

    banner("4. /devops with Bearer <jwt> (expect SUCCESS)")
    r = httpx.get(f"{GATEWAY}/devops/config/gateway", headers=bearer_headers)
    print(f"  GET  /devops/config/gateway  -> {r.status_code}")
    r.raise_for_status()
    print(
        "  Confirmed: /devops accepts the JWT because DEVOPS_AUTHENTICATION_METHOD"
        "=oauth2 is set, a devops-specific issuer is registered, and the"
        " resulting Ditto subject `ditto:ditto` is in DEVOPS_OAUTH2_SUBJECTS."
    )

    banner("5. /devops with HTTP Basic Auth devops:foobar (expect FAILURE)")
    r = httpx.get(f"{GATEWAY}/devops/config/gateway", auth=("devops", "foobar"))
    print(f"  GET  /devops/config/gateway  -> {r.status_code}")
    if r.status_code == 200:
        print("  UNEXPECTED: Basic Auth was accepted on /devops in oauth2 mode")
        sys.exit(1)
    print(
        "  Confirmed: in oauth2 mode the gateway no longer accepts Basic Auth"
        " on /devops - basic and oauth2 are mutually exclusive on this route."
    )

    banner("Done")


if __name__ == "__main__":
    main()
