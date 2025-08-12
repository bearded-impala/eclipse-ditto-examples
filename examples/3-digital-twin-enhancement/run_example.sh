#!/bin/bash
set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

log_section() {
  echo
  echo "=================================================="
  echo "[EXAMPLE 3: DIGITAL TWIN ENHANCEMENT] $1"
  echo "=================================================="
}

log_section "Creating Policy"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_POLICIES_API/$VEHICLE_001_POLICY_ID" \
  -d @policy.json

log_section "Creating Thing"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$VEHICLE_001_ID" \
  -d @thing.json

log_section "Simulating External Service (Update Weather Data)"
WEATHER_DATA='{"temperature": 18.2, "conditions": "Cloudy", "windSpeed": 15, "lastUpdated": "2025-07-22T09:15:00Z"}'
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$VEHICLE_001_ID/features/weather/properties" \
  -d "$WEATHER_DATA"

log_section "Retrieving Digital Twin State"
curl -s -X GET -u "$DITTO_AUTH" \
  "$DITTO_THINGS_API/$VEHICLE_001_ID" | jq .

echo
log_section "Example 3 completed!" 