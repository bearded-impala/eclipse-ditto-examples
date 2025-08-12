#!/bin/bash
set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

log_section() {
  echo
  echo "=================================================="
  echo "[EXAMPLE 2: REMOTE DEVICE CONTROL] $1"
  echo "=================================================="
}

log_section "Creating Policy"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_POLICIES_API/$LIGHT_001_POLICY_ID" \
  -d @policy.json

log_section "Creating Thing"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$LIGHT_001_ID" \
  -d @thing.json

log_section "Updating Desired State (onOff)"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$LIGHT_001_ID/features/onOff/properties/status/desired" \
  -d 'true'

log_section "Retrieving Digital Twin State"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_THINGS_API/$LIGHT_001_ID" | jq .

echo
log_section "Example 2 completed!" 