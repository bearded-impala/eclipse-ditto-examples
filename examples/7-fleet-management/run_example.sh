#!/bin/bash
set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

log_section() {
  echo
  echo "=================================================="
  echo "[EXAMPLE 8: FLEET MANAGEMENT] $1"
  echo "=================================================="
}

log_section "Creating Policy"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_POLICIES_API/$SENSOR_POLICY_ID" \
  -d @policy.json

log_section "Bulk Creating Things"
chmod +x bulk_create_things.sh
./bulk_create_things.sh

log_section "Update sensor-002 reported state"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$SENSOR_002_ID/features/humidity/properties/value" \
  -d '70.1'

log_section "Search: Find all things"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_SEARCH_API" | jq .

log_section "Search: Find all things with manufacturer: 'ABC'"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_SEARCH_API?filter=eq(attributes/manufacturer,'ABC')" | jq .

log_section "Search: Find all things where temperature > 20 Celsius"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_SEARCH_API?filter=gt(features/temperature/properties/value,20)" | jq .

log_section "Search: Find all things in the 'Living Room'"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_SEARCH_API?filter=eq(attributes/location,'Living%20Room')" | jq .

log_section "Search: Combine queries (temperature > 20 AND location = 'Living Room')"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_SEARCH_API?filter=and(gt(features/temperature/properties/value,20),eq(attributes/location,'Living%20Room'))" | jq .

echo
log_section "Example 8 completed!" 