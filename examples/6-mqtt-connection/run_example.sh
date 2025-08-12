#!/bin/bash

set -euo pipefail

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

# === Cleanup on EXIT or INT ===
cleanup() {
  echo "🧹 Cleaning up..."
  docker rm -f mosquitto-broker >/dev/null 2>&1 || true
  echo "Cleanup done."
}
trap cleanup EXIT INT

# === Start MQTT Broker ===
echo "🚀 Starting MQTT broker..."
uv run poe start-mqtt-broker

# Wait for broker to be ready
echo "⏳ Waiting for MQTT broker to be ready..."
sleep 3

# === Provision Ditto ===
echo "🔐 Creating Ditto policy..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
  "$DITTO_POLICIES_API/$TEST_POLICY_ID" \
  -u "$DITTO_AUTH" \
  -H 'Content-Type: application/json' \
  -d @policy.json)
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
  echo "❌ Failed to create policy (HTTP $http_code)"
  exit 1
fi

echo "📦 Creating Ditto thing 'sensor01'..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
  "$DITTO_THINGS_API/$SENSOR01_ID" \
  -u "$DITTO_AUTH" \
  -H 'Content-Type: application/json' \
  -d @"sensor01.json")
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
  echo "❌ Failed to create thing sensor01 (HTTP $http_code)"
  exit 1
fi

echo "📦 Creating Ditto thing 'sensor02'..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
  "$DITTO_THINGS_API/$SENSOR02_ID" \
  -u "$DITTO_AUTH" \
  -H 'Content-Type: application/json' \
  -d @sensor02.json)
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
  echo "❌ Failed to create thing sensor02 (HTTP $http_code)"
  exit 1
fi

echo "🔗 Creating MQTT source connection..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$DITTO_DEVOPS_API/piggyback/connectivity?timeout=$CONNECTION_TIMEOUT" \
  -u "$DITTO_DEVOPS_AUTH" \
  -H 'Content-Type: application/json' \
  -d @connection_source.json)
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
  echo "❌ Failed to create MQTT source connection (HTTP $http_code)"
  exit 1
fi

echo "🔗 Creating MQTT target connection..."
http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  "$DITTO_DEVOPS_API/piggyback/connectivity?timeout=$CONNECTION_TIMEOUT" \
  -u "$DITTO_DEVOPS_AUTH" \
  -H 'Content-Type: application/json' \
  -d @connection_target.json)
if [ "$http_code" -lt 200 ] || [ "$http_code" -ge 300 ]; then
  echo "❌ Failed to create MQTT target connection (HTTP $http_code)"
  exit 1
fi

# === Done ===
trap - EXIT INT  # clear trap so cleanup doesn't remove containers now
echo "✅ Setup Complete!"

cat <<EOF

🧪 To test:

🦟 bash into mosquitto container
  docker exec -it mosquitto-broker /bin/sh

📤 Publish an update:
  mosquitto_pub -h host.docker.internal -t $MQTT_TOPIC_PREFIX/sensor01 -m '{"temperature": 56, "humidity": 86, "thingId": "$SENSOR01_ID"}'

EOF
