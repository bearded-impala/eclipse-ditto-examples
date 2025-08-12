#!/bin/bash

# Load environment variables from .env file
# This script should be sourced by other scripts: source scripts/load_env.sh

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Path to the .env file
ENV_FILE="$PROJECT_ROOT/.env"

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found at $ENV_FILE"
    echo "Please create a .env file in the project root directory"
    exit 1
fi

# Load environment variables from .env file
# This handles variable substitution within the .env file
while IFS= read -r line || [ -n "$line" ]; do
    # Skip comments and empty lines
    if [[ $line =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
        continue
    fi
    
    # Export the variable
    export "$line"
done < "$ENV_FILE"

# Resolve nested variable references
# This is a simple implementation - for more complex cases, consider using a proper env file parser
export DITTO_BASE_URL="${DITTO_PROTOCOL}://${DITTO_HOST}:${DITTO_PORT}"
export DITTO_AUTH="${DITTO_USERNAME}:${DITTO_PASSWORD}"
export DITTO_DEVOPS_AUTH="${DITTO_DEVOPS_USERNAME}:${DITTO_DEVOPS_PASSWORD}"
export DITTO_API_BASE="${DITTO_BASE_URL}/api/2"
export DITTO_THINGS_API="${DITTO_API_BASE}/things"
export DITTO_POLICIES_API="${DITTO_API_BASE}/policies"
export DITTO_SEARCH_API="${DITTO_API_BASE}/search/things"
export DITTO_DEVOPS_API="${DITTO_BASE_URL}/devops"

# Thing IDs
export SENSOR_001_ID="${DITTO_NAMESPACE}:sensor-001"
export LIGHT_001_ID="${DITTO_NAMESPACE}:light-001"
export SENSOR_002_ID="${DITTO_NAMESPACE}:sensor-002"
export SENSOR_003_ID="${DITTO_NAMESPACE}:sensor-003"
export SENSOR_004_ID="${DITTO_NAMESPACE}:sensor-004"
export SENSOR_005_ID="${DITTO_NAMESPACE}:sensor-005"
export SENSOR_006_ID="${DITTO_NAMESPACE}:sensor-006"
export TEST_SENSOR_ID="${DITTO_SENSORS_NAMESPACE}:sensor"
export SENSOR01_ID="${DITTO_SENSORS_NAMESPACE}:sensor01"
export SENSOR02_ID="${DITTO_SENSORS_NAMESPACE}:sensor02"
export VEHICLE_001_ID="${DITTO_NAMESPACE}:vehicle-001"
export DOORLOCK_001_ID="${DITTO_NAMESPACE}:doorlock-001"
export KETTLE_001_ID="${DITTO_NAMESPACE}:kettle-001"

# Policy IDs
export SENSOR_001_POLICY_ID="${DITTO_NAMESPACE}:sensor-001-policy"
export LIGHT_001_POLICY_ID="${DITTO_NAMESPACE}:light-001-policy"
export SENSOR_POLICY_ID="${DITTO_NAMESPACE}:sensor-policy"
export TEST_POLICY_ID="${DITTO_TEST_NAMESPACE}:policy"
export VEHICLE_001_POLICY_ID="${DITTO_NAMESPACE}:vehicle-001-policy"
export DOORLOCK_001_POLICY_ID="${DITTO_NAMESPACE}:doorlock-001-policy"
export KETTLE_001_POLICY_ID="${DITTO_NAMESPACE}:kettle-001-policy"

# MQTT Configuration
export MQTT_TOPIC_PREFIX="${DITTO_SENSORS_NAMESPACE}"

echo "✅ Environment variables loaded from $ENV_FILE"
