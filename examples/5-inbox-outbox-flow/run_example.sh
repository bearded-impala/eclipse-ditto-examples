#!/bin/bash
set -e

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

log_section() {
  echo
  echo "=================================================="
  echo "[EXAMPLE 5: INBOX-OUTBOX FLOW] $1"
  echo "=================================================="
}

log_section "Creating Policy"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_POLICIES_API/$KETTLE_001_POLICY_ID" \
  -d @policy.json

log_section "Creating Thing"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$KETTLE_001_ID" \
  -d @thing.json

log_section "Creating Connection"
curl -X POST -i -u "$DITTO_DEVOPS_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_API_BASE/connections" \
  -d @connection.json

log_section "App sets desired temperature (Outbox action)"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$KETTLE_001_ID/features/temperature/properties/desired" \
  -d '95'

log_section "Device reports temperature (Telemetry/Inbox action)"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$KETTLE_001_ID/features/temperature/properties/value" \
  -d '92.5'

log_section "Device sends activity event (Event/Inbox action)"
curl -X PUT -i -u "$DITTO_AUTH" -H 'Content-Type: application/json' \
  "$DITTO_THINGS_API/$KETTLE_001_ID/features/activityLog/properties/lastEvent" \
  -d '"Boiling started"'

log_section "Polling Thing's State (5 times, 2s interval)"
for i in {1..5}; do
  echo "--- Poll #$i ---"
  curl -s -X GET -u "$DITTO_AUTH" \
    "$DITTO_THINGS_API/$KETTLE_001_ID" | jq .
  sleep 2
done

echo
log_section "Example 5 completed!" 