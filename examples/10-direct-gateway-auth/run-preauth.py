#!/usr/bin/env python3
"""
Example 10 / Variant A - "Basic-auth style" via the pre-authenticated header.

Runs from the host. The compose stack (`docker-compose-e10-preauth.yml`)
publishes the gateway on port 8080, so `http://localhost:8080` is sufficient.
"""

import json
import sys
from pathlib import Path
from typing import Any

import httpx

GATEWAY = "http://localhost:8080"
PRE_AUTH_SUBJECT = "nginx:ditto"

HERE = Path(__file__).parent
POLICY: dict[str, Any] = json.loads((HERE / "policy-preauth.json").read_text())
THING: dict[str, Any] = json.loads((HERE / "thing-preauth.json").read_text())
POLICY_ID: str = POLICY["policyId"]
THING_ID: str = THING["thingId"]


def banner(text: str) -> None:
    print(f"\n=== {text} ===")


def main() -> None:
    pre_auth_headers: dict[str, str] = {"x-ditto-pre-authenticated": PRE_AUTH_SUBJECT}

    banner("1. /api/2 with pre-authenticated header (expect SUCCESS)")
    r = httpx.put(
        f"{GATEWAY}/api/2/policies/{POLICY_ID}", json=POLICY, headers=pre_auth_headers
    )
    print(f"  PUT  /api/2/policies/{POLICY_ID}  -> {r.status_code}")
    r.raise_for_status()

    r = httpx.put(
        f"{GATEWAY}/api/2/things/{THING_ID}", json=THING, headers=pre_auth_headers
    )
    print(f"  PUT  /api/2/things/{THING_ID}  -> {r.status_code}")
    r.raise_for_status()

    r = httpx.get(f"{GATEWAY}/api/2/things/{THING_ID}", headers=pre_auth_headers)
    print(f"  GET  /api/2/things/{THING_ID}  -> {r.status_code}")
    r.raise_for_status()

    banner("2. /api/2 with HTTP Basic Auth direct to gateway (expect FAILURE)")
    r = httpx.get(f"{GATEWAY}/api/2/things/{THING_ID}", auth=("ditto", "ditto"))
    print(f"  GET  /api/2/things/{THING_ID}  -> {r.status_code}")
    if r.status_code == 200:
        print("  UNEXPECTED: Basic Auth was accepted on /api/2 by the gateway")
        sys.exit(1)
    print(
        "  Confirmed: the gateway has no native HTTP Basic Auth on /api/2."
        " In a normal stack, nginx terminates Basic and forwards as a pre-auth"
        " header (which is call #1)."
    )

    banner("3. /devops with pre-authenticated header (expect FAILURE)")
    r = httpx.get(f"{GATEWAY}/devops/config/gateway", headers=pre_auth_headers)
    print(f"  GET  /devops/config/gateway  -> {r.status_code}")
    if r.status_code == 200:
        print("  UNEXPECTED: pre-auth header was accepted on /devops")
        sys.exit(1)
    print("  Confirmed: /devops never honors the pre-auth header.")

    banner("4. /devops with HTTP Basic Auth devops:foobar (expect SUCCESS)")
    r = httpx.get(f"{GATEWAY}/devops/config/gateway", auth=("devops", "foobar"))
    print(f"  GET  /devops/config/gateway  -> {r.status_code}")
    r.raise_for_status()
    print(
        "  Confirmed: /devops uses its own auth realm. With"
        " DEVOPS_AUTHENTICATION_METHOD=basic (default) the gateway natively"
        " accepts HTTP Basic Auth with user `devops`."
    )

    banner("Done")


if __name__ == "__main__":
    main()
