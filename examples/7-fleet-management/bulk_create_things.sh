#!/bin/bash

# Load environment variables
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$PROJECT_ROOT/utils/load_env.sh"

# Folder containing the JSON files
FOLDER="$FLEET_FOLDER"

# Loop over all .json files in the folder
for FILE in "$FOLDER"/*.json; do
  # Extract thingId from the file (assumes it's in the JSON)
  THING_ID=$(jq -r '.thingId' "$FILE")

  if [ "$THING_ID" == "null" ]; then
    echo "❌ Skipping $FILE - no 'thingId' found"
    continue
  fi

  echo "📡 Uploading $THING_ID from $FILE..."

  curl -X PUT -i -u "$DITTO_AUTH" \
    -H 'Content-Type: application/json' \
    "$DITTO_THINGS_API/$THING_ID" \
    -d @"$FILE"
  
  echo "✅ Done with $THING_ID"
  echo "----------------------------"
done
