# Introduction

## Goal

Remotely lock/unlock a smart door. We want to ensure the command is eventually delivered and confirmed, even if the door lock is temporarily offline. We'll use the Outbox Pattern focusing on the desired vs. reported state synchronization.

### Flow

1. Policy: Define permissions for the application and the device.
2. Thing: Create a digital twin for the door lock with a lockState feature, initially UNLOCKED.
3. Application issues command: An application sets the desired state of lockState to LOCKED.
4. Ditto detects change & sends command (simulated): In a real scenario, a Ditto connection would pick up this desired state change and send an MQTT command to the physical lock. For this curl example, we will simulate the device receiving the command.
5. Device receives command & reports actual state: The physical lock receives the command, changes its state, and then reports its new actual state (LOCKED) back to Ditto's value field.
6. Verify Synchronization: Check the digital twin; desired and reported states should now match.

#### Create Policy

This policy requires basic authentication.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/policies/org.eclipse.ditto:doorlock-001-policy \
  -d @policy.json
```

#### Create Things

Create a Thing description in eclipse-ditto.
```bash
curl -X PUT -i -u ditto:ditto -H 'Content-Type: application/json' \
  http://localhost:8080/api/2/things/org.eclipse.ditto:doorlock-001 \
  -d @thing.json
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

### 3. Verify Sync:

Retrieve the full state of the digital twin.

```bash
curl -s -X GET -u ditto:ditto \
  http://localhost:8080/api/2/things/org.eclipse.ditto:doorlock-001 | jq .
```
