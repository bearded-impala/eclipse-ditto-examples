# Introduction

## Goal

Simulate an application polling a Smart Kettle's digital twin to:
1. Check if a desired temperature command is pending (outbox concept).
2. Read the latest reported temperature and any incoming activity messages (inbox concept).

### Flow

1. Policy: Define permissions for the application and the kettle.
2. Thing: Create a digital twin for the Smart Kettle with:
3. A temperature feature with value (reported by device) and desired (set by app).
4. An activityLog feature to act as a simple "inbox" for device events.
5. App sets desired temperature (Outbox action): The application sends a command by setting the desired state.
6. Device reports temperature (Telemetry/Inbox action): The device simulates reporting its current temperature.
7. Device sends an activity event (Event/Inbox action): The device simulates sending a specific activity message.
8. Polling: The application repeatedly fetches the thing's state to observe changes in desired, value, and activityLog.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/policies/org.eclipse.ditto:kettle-001-policy \
  -d @policy.json
```

#### Create Thing

This defines our digital twin for kettle-001 with a temperature feature and an activityLog feature.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:kettle-001 \
  -d @thing.json
```

#### Create Connection

This is the crucial part. It configures Ditto to send all "thing changed" events to the Mosquitto broker.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/connections \
  -d @connection.json
```
targets: Defines what Ditto sends out.
  - address: "ditto/events/thing": This is the base MQTT topic to which Ditto will publish the events. The actual topic will be ditto/events/thing/<ditto-internal-topic>.
  - topics: ["_/_/things/twin/events"]: This tells Ditto to internally subscribe to its own "thing twin events" and forward them to the MQTT broker. This includes all changes to desired, value, attributes, features, etc.

### 3. Setup an MQTT Broker

eclipse-mosquitto is an MQTT broker implementation.

```bash
uv run poe start-mqtt-broker
```

## Test the Example

### 1. Application issues command (sets desired state - Outbox):

The application wants to lock the door. It writes the desired state to the twin. This is the "outbox" action.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:doorlock-001/features/lockState/properties/status/desired \
  -d '"LOCKED"'
```
Expected state after this command: The desired field under lockState/properties/status will be LOCKED, while the value field will remain UNLOCKED. This indicates a pending command.

### 2. Simulate Device Action and Report (Completing the Outbox cycle):

In a real scenario, a Ditto connection (e.g., via MQTT) would pick up the change to desired.status and send a command to the physical door lock. The door lock would receive it, physically lock, and then send a message back to Ditto indicating its new actual state.

For our curl test, we manually simulate the device reporting its actual state after receiving and acting on the command.

```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:doorlock-001/features/lockState/properties/status/value \
  -d '"LOCKED"'
```

### 3. Verify Synchronization:

Retrieve the full state of the digital twin.

```bash
curl -s -X GET -u ditto:ditto \
  http://localhost:8080/api/2/things/org.eclipse.ditto:doorlock-001 | jq .
```
